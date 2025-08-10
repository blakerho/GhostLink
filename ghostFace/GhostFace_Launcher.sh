#!/bin/bash

# GhostFace Launcher - All-in-One Solution
# This script launches the server and opens the browser automatically

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the ghostFace directory
cd "$SCRIPT_DIR"

# Display a notification that we're starting
osascript -e 'display notification "Starting GhostFace web server..." with title "GhostFace"'

# Start the Python server in the background
echo "🚀 Starting GhostFace web server..."
python3 launch.py > /dev/null 2>&1 &
SERVER_PID=$!

# Wait a moment for the server to start
sleep 3

# Check if server is running
if kill -0 $SERVER_PID 2>/dev/null; then
    # Open the browser to the correct URL
    echo "🌐 Opening browser..."
    open "http://localhost:5001"
    
    # Display success notification
    osascript -e 'display notification "GhostFace is ready! Browser should open automatically." with title "GhostFace"'
    
    echo "✅ GhostFace is running!"
    echo "📱 Browser should open automatically to http://localhost:5001"
    echo "🛑 To stop the server, close this terminal window or press Ctrl+C"
    
    # Keep the script running to maintain the server process
    wait $SERVER_PID
else
    echo "❌ Failed to start GhostFace server"
    osascript -e 'display notification "Failed to start GhostFace server" with title "GhostFace Error"'
    exit 1
fi
