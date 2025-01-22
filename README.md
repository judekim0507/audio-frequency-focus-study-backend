# Audio Frequency Focus Study (Backend)

A Python-based backend service for processing EEG data from Muse headbands to study the effects of audio frequencies on focus levels.

## Overview

This backend service processes real-time EEG data from any Muse headband, calculating focus/engagement levels using the Beta/(Alpha+Theta) ratio. It provides:

- Real-time EEG data processing
- Focus level calculations
- WebSocket API for frontend communication
- Baseline calibration functionality

## Features

- **EEG Processing:**
  - Real-time signal processing
  - Band power calculations (Delta, Theta, Alpha, Beta)
  - Focus level normalization
  - Moving average smoothing

- **Data Collection:**
  - Baseline calibration
  - Continuous EEG monitoring
  - Engagement index calculation
  - Signal quality checking

- **API Features:**
  - WebSocket real-time data streaming
  - Connection status monitoring
  - Error handling and recovery
  - Calibration endpoints

## Technical Details

- **Backend Stack:**
  - Python 3.8+
  - FastAPI for WebSocket server
  - NumPy for numerical processing
  - SciPy for signal processing
  - Muse-LSL for EEG data streaming

- **Signal Processing:**
  - Welch's method for power spectral density
  - Simpson's rule for band power integration
  - Beta/(Alpha+Theta) engagement index
  - Adaptive baseline normalization

## Setup

1. Clone the repository:

```bash
git clone https://github.com/judekim0507/audio-frequency-focus-study-backend.git
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Connect Muse headband via Bluetooth

4. Start the server:

```bash
python src/main.py
```

## Environment Variables

#### Experiment Settings
TEST_DURATION=30 # Duration of each test session
REST_DURATION=2 # Rest period between sessions
PREP_DURATION=3 # Preparation time before session
#### Logging
LOG_LEVEL=INFO
Data Paths
DATA_DIR=data # Directory for raw data storage
RESULTS_DIR=results # Directory for processed results
#### Frequencies to test (Hz)
FREQ_LOW_HUM=432
FREQ_NATURE=528
FREQ_STUDY=639


## API Documentation

### WebSocket Endpoints

- `ws://localhost:8000/ws`
  - Streams real-time focus levels
  - Handles calibration requests
  - Provides connection status

### Message Types
```json
// Focus Level Update
{
  "connected": true,
  "engagement_index": 1.25,
  "focus_level": 65.5
}
```

```json
// Calibration Complete
{
  "type": "calibration_complete",
  "min": 0.3,
  "max": 0.75
}
```


## Signal Processing Pipeline

1. Raw EEG data collection
2. Band power calculation
   - Delta (0.5-4 Hz)
   - Theta (4-8 Hz)
   - Alpha (8-13 Hz)
   - Beta (13-30 Hz)
3. Engagement index calculation: β/(α+θ)
4. Smoothing and normalization
5. Real-time streaming

## Requirements

- Python 3.8+
- Muse EEG headband
- Bluetooth connectivity
- Compatible operating system (Windows/macOS/Linux)

## License

MIT License

## Contributors

- Jude Kim - Burnaby North Secondary School

## Related Projects

- [Frontend Application](https://github.com/judekim0507/audio-frequency-focus-study-frontend)