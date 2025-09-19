#!/bin/bash

# Face Control Runner Script
# Activates virtual environment and runs the face control application

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Virtual environment directory
VENV_DIR="venv"

# Check if virtual environment exists, create if not
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run the face control application
echo "Starting Face Control System..."
python face.py

# Deactivate virtual environment when done
deactivate