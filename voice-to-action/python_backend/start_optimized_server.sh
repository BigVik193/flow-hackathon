#!/bin/bash

# Conversational Voice Agent Startup Script v5.0
# Sets up environment with LangChain Memory + Anthropic Claude

set -e

echo "🚀 Starting Conversational Voice Agent Backend v5.0..."
echo "💬 LangChain Memory + Anthropic Claude + Learning Foundation"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/.venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Load environment variables from .env file if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "📄 Loading environment variables from .env file..."
    export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies from requirements.txt
echo "📥 Installing dependencies from requirements.txt..."
pip install -r "$SCRIPT_DIR/requirements.txt"

# Check for required environment variables
echo "🔍 Checking environment variables..."

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set"
    echo "Please set it: export ANTHROPIC_API_KEY='your-key'"
fi

# Add system optimizations for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Applying macOS optimizations..."
    # Increase file descriptor limits for better performance
    ulimit -n 10240 2>/dev/null || true
fi

echo ""
echo "✅ Setup complete! Starting conversational server..."
echo ""
echo "🎯 Features:"
echo "   • LangChain RunnableWithMessageHistory for conversation memory"
echo "   • Anthropic Claude Sonnet 4 for intelligent responses"
echo "   • Session-based conversation persistence"
echo "   • MiniMax TTS integration for voice responses"
echo "   • Learning-ready foundation for pattern analysis"
echo ""
echo "📊 Capabilities:"
echo "   • Maintains context across conversation sessions"
echo "   • Multiple conversation threads support"
echo "   • Voice synthesis with audio URL responses"
echo "   • RESTful API for easy integration"
echo ""

# Start the conversational server
echo "🚀 Launching conversational server on http://localhost:8000..."
python "$SCRIPT_DIR/optimized_browser_agent_api.py"