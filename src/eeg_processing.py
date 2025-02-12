# eeg_processing.py

from pylsl import StreamInlet
import numpy as np
from scipy.signal import welch
from scipy.integrate import simpson
import time

def collect_eeg_data(inlet: StreamInlet, window_length: int, fs: int):
    n_samples = int(window_length * fs)
    eeg_data = []

    while len(eeg_data) < n_samples:
        chunk, timestamps = inlet.pull_chunk(timeout=1.0, max_samples=n_samples - len(eeg_data))
        if timestamps:
            eeg_data.extend(chunk)
    return np.array(eeg_data)

def bandpower(data, fs, band):
    """
    Calculate the average power of the signal x in a specific frequency band.
    """
    f, psd = welch(data, fs, nperseg=len(data))
    # Find closest indices of band in frequency vector
    idx_band = np.logical_and(f >= band[0], f <= band[1])
    
    # Get the frequencies and PSD values within our band of interest
    freq_band = f[idx_band]
    psd_band = psd[idx_band]
    
    # Calculate absolute power by approximating the integral
    # simpson needs y values first, then x values
    bp = simpson(y=psd_band, x=freq_band) if len(freq_band) > 0 else 0
    
    return bp

def normalize_focus(engagement_index, min_value, max_value):
    if max_value == min_value:
        focus_level = 50.0
    else:
        # If engagement is above max, scale the range
        if engagement_index > max_value:
            max_value = engagement_index
        
        focus_level = (engagement_index - min_value) / (max_value - min_value)
        focus_level = np.clip(focus_level, 0, 1)
        focus_level = focus_level * 100
    return focus_level

def collect_relaxed_baseline(inlet, duration=120):
    """Collect baseline EEG data during relaxed state (eyes closed)"""
    engagement_indices = []
    
    print("Collecting relaxed baseline... Please close your eyes and relax.")
    end_time = time.time() + duration
    while time.time() < end_time:
        eeg_data = collect_eeg_data(inlet, 2, 256)
        eeg_mean = np.mean(eeg_data, axis=1)
        
        theta = bandpower(eeg_mean, 256, [4, 8])
        alpha = bandpower(eeg_mean, 256, [8, 13])
        beta = bandpower(eeg_mean, 256, [13, 30])
        
        engagement_index = beta / (alpha + theta)
        engagement_indices.append(engagement_index)
    
    relaxed_baseline = np.mean(engagement_indices)
    # Focused baseline is typically 2-3x higher than relaxed
    focused_baseline = relaxed_baseline * 2.5
    
    return relaxed_baseline, focused_baseline

def get_average_baseline():
    # Increase the range to handle higher engagement indices
    min_engagement = 0.3
    max_engagement = min_engagement * 4.0  # Increase multiplier from 2.5 to 4.0
    return min_engagement, max_engagement