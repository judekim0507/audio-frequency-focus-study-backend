# main.py

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from pylsl import StreamInlet, resolve_byprop
import numpy as np
import asyncio
from eeg_processing import (
    collect_eeg_data,
    bandpower,
    normalize_focus,
    get_average_baseline,
    collect_relaxed_baseline,
)
from muselsl import stream, list_muses
import uvicorn
from collections import deque
import json

app = FastAPI()

# Sampling frequency and window length
fs = 256  # Sampling frequency (Hz)
window_length = 2  # Window length (seconds)

# Initialize EEG stream
is_eeg_connected = False

try:
    print("Connecting to EEG stream...")
    streams = resolve_byprop('type', 'EEG', timeout=5)
    if len(streams) == 0:
        print("No EEG stream found.")
        is_eeg_connected = False
    else:
        inlet = StreamInlet(streams[0], max_chunklen=12)
        is_eeg_connected = True
        print("Successfully connected to EEG stream.")
except Exception as e:
    print(f"Error connecting to EEG stream: {e}")
    is_eeg_connected = False

# Use average baseline values
min_value, max_value = get_average_baseline()

print("Using average baseline values:")
print(f"Minimum Engagement Index (Low Focus): {min_value:.4f}")
print(f"Maximum Engagement Index (High Focus): {max_value:.4f}")

latest_data = {
    "engagement_index": 0,
    "focus_level": 0,
    "band_powers": {
        "delta": 0,
        "theta": 0,
        "alpha": 0,
        "beta": 0
    },
    "eeg_mean": None
}

SMOOTHING_WINDOW_SIZE = 5  # Number of samples to average
MAX_CHANGE_THRESHOLD = 0.15  # Maximum allowed change between consecutive readings (50%)
MINIMUM_SAMPLES_REQUIRED = 3  # Wait for at least 3 samples before sending data
has_enough_samples = False  # Flag to track if we have enough samples

focus_history = deque(maxlen=SMOOTHING_WINDOW_SIZE)
band_power_history = {
    'delta': deque(maxlen=SMOOTHING_WINDOW_SIZE),
    'theta': deque(maxlen=SMOOTHING_WINDOW_SIZE),
    'alpha': deque(maxlen=SMOOTHING_WINDOW_SIZE),
    'beta': deque(maxlen=SMOOTHING_WINDOW_SIZE)
}

def smooth_data(new_value, history):
    history.append(new_value)
    return np.mean(history)

def limit_change(new_value, previous_value, max_change):
    if previous_value is None:
        return new_value
    max_allowed_change = previous_value * max_change
    change = new_value - previous_value
    if abs(change) > max_allowed_change:
        if change > 0:
            return previous_value + max_allowed_change
        else:
            return previous_value - max_allowed_change
    return new_value

async def process_eeg_data():
    global has_enough_samples
    previous_focus = None
    sample_count = 0
    
    while True:
        # Collect and process EEG data
        eeg_data = collect_eeg_data(inlet, window_length, fs)
        eeg_mean = np.mean(eeg_data, axis=1)

        # Calculate band powers
        delta_power = bandpower(eeg_mean, fs, [0.5, 4])
        theta_power = bandpower(eeg_mean, fs, [4, 8])
        alpha_power = bandpower(eeg_mean, fs, [8, 13])
        beta_power = bandpower(eeg_mean, fs, [13, 30])

        # Debug print
        print("\nRaw Band Powers:")
        print(f"Delta: {delta_power:.6f}")
        print(f"Theta: {theta_power:.6f}")
        print(f"Alpha: {alpha_power:.6f}")
        print(f"Beta: {beta_power:.6f}")

        # Smooth band powers
        delta_power = smooth_data(delta_power, band_power_history['delta'])
        theta_power = smooth_data(theta_power, band_power_history['theta'])
        alpha_power = smooth_data(alpha_power, band_power_history['alpha'])
        beta_power = smooth_data(beta_power, band_power_history['beta'])

        # Compute engagement index
        engagement_index = beta_power / (alpha_power + theta_power)
        focus_level_percentage = normalize_focus(engagement_index, min_value, max_value)

        # Smooth and limit the focus level changes
        focus_level_percentage = smooth_data(focus_level_percentage, focus_history)
        focus_level_percentage = limit_change(
            focus_level_percentage, 
            previous_focus, 
            MAX_CHANGE_THRESHOLD
        )
        previous_focus = focus_level_percentage

        # Update sample count and check if we have enough samples
        sample_count += 1
        if sample_count >= MINIMUM_SAMPLES_REQUIRED:
            has_enough_samples = True

        # Update global latest_data with all values
        latest_data.update({
            "engagement_index": float(engagement_index),
            "focus_level": float(focus_level_percentage),
            "band_powers": {
                "delta": float(delta_power),
                "theta": float(theta_power),
                "alpha": float(alpha_power),
                "beta": float(beta_power)
            },
            "eeg_mean": eeg_mean.tolist()
        })

        print(f"\nProcessed EEG Data:")
        print(f"Raw Engagement Index: {engagement_index:.4f}")
        print(f"Smoothed Focus Level: {focus_level_percentage:.2f}%")
        print(f"Band Powers - Delta: {delta_power:.4f}, Theta: {theta_power:.4f}, Alpha: {alpha_power:.4f}, Beta: {beta_power:.4f}")
        print("-" * 50)

        # Debug print the data being sent
        print("\nSending data:")
        print(json.dumps(latest_data, indent=2))

        await asyncio.sleep(window_length)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_json()
            
            if message.get('type') == 'start_calibration':
                print("Starting baseline calibration...")
                # Use the calibration function
                global min_value, max_value
                min_value, max_value = collect_relaxed_baseline(inlet)
                
                print(f"Calibration complete:")
                print(f"Relaxed baseline (min): {min_value:.4f}")
                print(f"Focused baseline (max): {max_value:.4f}")
                
                # Send calibration results back to frontend
                await websocket.send_json({
                    "type": "calibration_complete",
                    "min": float(min_value),
                    "max": float(max_value)
                })
            
            if not is_eeg_connected:
                await websocket.send_json({
                    "connected": False,
                    "message": "EEG stream not connected"
                })
            elif has_enough_samples:
                data = {
                    "connected": True,
                    "engagement_index": latest_data["engagement_index"],
                    "focus_level": latest_data["focus_level"]
                }
                print(f"Sending - Engagement Index: {data['engagement_index']:.4f}, Focus Level: {data['focus_level']:.2f}%")
                await websocket.send_json(data)
            else:
                await websocket.send_json({
                    "connected": False,
                    "message": "Collecting initial samples..."
                })
                
            await asyncio.sleep(window_length)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_eeg_data())

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000)