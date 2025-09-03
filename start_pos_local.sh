#!/bin/bash

echo "========================================="
echo "  POS System with M-Pesa Integration"
echo "========================================="
echo

# Change to the script directory
cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.7+ and try again"
    exit 1
fi

# Check if virtual environment exists
if [ -f "env/bin/activate" ]; then
    echo "Activating virtual environment..."
    source env/bin/activate
elif [ -f "../env/bin/activate" ]; then
    echo "Activating virtual environment..."
    source ../env/bin/activate
else
    echo "WARNING: Virtual environment not found"
    echo "Using system Python..."
fi

# Install pyngrok if not already installed
echo "Checking for pyngrok..."
if ! python3 -c "import pyngrok" &> /dev/null; then
    echo "Installing pyngrok for ngrok integration..."
    pip3 install pyngrok
fi

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo
    echo "WARNING: ngrok is not installed or not in PATH"
    echo
    echo "To enable M-Pesa payments, please:"
    echo "1. Download ngrok from https://ngrok.com/download"
    echo "2. Install ngrok to your PATH"
    echo "3. Sign up at https://ngrok.com and get your auth token"
    echo "4. Run: ngrok authtoken YOUR_AUTH_TOKEN"
    echo
    echo "Continuing without ngrok - M-Pesa payments will not work"
    echo
    python3 start_pos_local.py --no-ngrok
else
    echo "Starting POS system with ngrok tunnel..."
    python3 start_pos_local.py
fi

echo
echo "Press Enter to exit..."
read