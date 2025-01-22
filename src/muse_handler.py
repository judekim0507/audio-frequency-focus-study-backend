from muselsl import stream, list_muses
from pylsl import StreamInlet, resolve_byprop
import numpy as np
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MuseHandler:
    def __init__(self):
        self.inlet = None
        
    def connect(self):
        """Connect to Muse headset"""
        try:
            muses = list_muses()
            if not muses:
                raise Exception("No Muse devices found!")
            
            logger.info("Connecting to Muse device...")
            stream(muses[0]['address'])
            
            logger.info("Looking for EEG stream...")
            streams = resolve_byprop('type', 'EEG', timeout=2)
            
            if len(streams) == 0:
                raise Exception("Can't find EEG stream!")
            
            self.inlet = StreamInlet(streams[0])
            logger.info("Successfully connected to Muse!")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Muse: {e}")
            return False
    
    def collect_data(self, duration):
        """Collect EEG data for specified duration"""
        if not self.inlet:
            raise Exception("Muse not connected!")
            
        eeg_data = []
        start_time = time.time()
        
        logger.info(f"Collecting {duration} seconds of EEG data...")
        while time.time() - start_time < duration:
            sample, timestamp = self.inlet.pull_sample()
            eeg_data.append(sample)
        
        return np.array(eeg_data)
    
    def close(self):
        """Close the connection"""
        if self.inlet:
            self.inlet.close_stream()
            logger.info("Muse connection closed")