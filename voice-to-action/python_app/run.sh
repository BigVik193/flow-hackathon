#!/bin/bash

# Control Flow Python App Launcher (Refactored Version)
# This script activates the virtual environment and runs the refactored application

set -e

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to app directory
cd "$DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "python3 -m venv venv"
    echo "source venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🚀 Activating virtual environment..."
source venv/bin/activate

# Check if backend is running
echo "🔍 Checking backend connection..."
if ! curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "⚠️ Backend not detected at http://127.0.0.1:8000"
    echo "Please start the backend first:"
    echo "cd ../python_backend && python optimized_browser_agent_api.py"
    echo ""
    echo "Continuing anyway - you can start the backend later..."
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "📁 Loading environment variables from .env..."
    # Export variables from .env, filtering out comments and empty lines
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
else
    echo "⚠️ .env file not found - some features may not work"
fi

# Set environment variables for better performance
export PYTHONUNBUFFERED=1
export QT_AUTO_SCREEN_SCALE_FACTOR=1

# Run the application
echo "🎤 Starting Control Flow Voice Agent..."
python main.py

echo "👋 Application closed"