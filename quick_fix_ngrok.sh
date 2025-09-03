#!/bin/bash

echo "🚀 Quick Ngrok ERR_NGROK_108 Fix"
echo "================================="

echo "🔍 Killing all ngrok processes..."
pkill -f ngrok 2>/dev/null
killall ngrok 2>/dev/null

echo "🧹 Clearing port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

echo "⏳ Waiting for cleanup..."
sleep 3

echo "🔍 Checking for remaining ngrok processes..."
if pgrep -f ngrok > /dev/null; then
    echo "⚠️  Some ngrok processes may still be running"
    echo "   Try running: sudo pkill -f ngrok"
else
    echo "✅ All ngrok processes terminated"
fi

echo ""
echo "✅ Cleanup completed!"
echo "Now you can run: python3 start_pos_local.py"