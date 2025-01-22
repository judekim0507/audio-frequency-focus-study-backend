#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Set required environment variables for Mac
export DYLD_LIBRARY_PATH=/opt/homebrew/lib

# Run the experiment
python src/experiment.py
