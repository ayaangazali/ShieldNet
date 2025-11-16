#!/bin/bash

# ShieldNet Backend Server Runner

# Get the directory where this script is located and cd into it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run ./quickstart.sh first."
    exit 1
fi

# Create logs directory
mkdir -p logs

echo "Starting ShieldNet Backend Server..."
echo "Working directory: $SCRIPT_DIR"
echo "API will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Start the server with auto-reload for development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
