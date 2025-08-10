#!/bin/bash

# GhostFace Robust Launcher
# This script ensures the server starts properly and opens the browser

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}👻 GhostFace Robust Launcher${NC}"
echo "=================================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}📁 Working directory:${NC} $SCRIPT_DIR"

# Function to check if server is running
check_server() {
    curl -s http://localhost:5001/api/health > /dev/null 2>&1
    return $?
}

# Function to kill existing processes
kill_existing() {
    echo -e "${YELLOW}🔄 Checking for existing processes...${NC}"
    PIDS=$(lsof -ti:5001 2>/dev/null || true)
    if [ ! -z "$PIDS" ]; then
        echo -e "${YELLOW}⚠️  Found existing processes on port 5001, killing them...${NC}"
        echo "$PIDS" | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo -e "${GREEN}✅ No existing processes found${NC}"
    fi
}

# Function to start server
start_server() {
    echo -e "${BLUE}🚀 Starting GhostFace server...${NC}"
    
    # Start the server in the background
    python3 launch.py > /tmp/ghostface.log 2>&1 &
    SERVER_PID=$!
    
    echo -e "${BLUE}📋 Server PID:${NC} $SERVER_PID"
    
    # Wait for server to start
    echo -e "${YELLOW}⏳ Waiting for server to start...${NC}"
    for i in {1..30}; do
        if check_server; then
            echo -e "${GREEN}✅ Server is running!${NC}"
            return 0
        fi
        sleep 1
        echo -n "."
    done
    
    echo -e "\n${RED}❌ Server failed to start within 30 seconds${NC}"
    return 1
}

# Function to open browser
open_browser() {
    echo -e "${BLUE}🌐 Opening browser...${NC}"
    open "http://localhost:5001"
    sleep 2
    echo -e "${GREEN}✅ Browser should be open now!${NC}"
}

# Main execution
main() {
    # Kill any existing processes
    kill_existing
    
    # Start the server
    if start_server; then
        # Open browser
        open_browser
        
        echo -e "${GREEN}🎉 GhostFace is ready!${NC}"
        echo -e "${BLUE}📋 Next steps:${NC}"
        echo "1. Use the web interface in your browser"
        echo "2. Select your GhostLink directory"
        echo "3. Choose encoding/decoding options"
        echo "4. Click the action buttons to process"
        echo ""
        echo -e "${YELLOW}💡 To stop the server, press Ctrl+C${NC}"
        
        # Keep the script running and monitor the server
        while true; do
            if ! check_server; then
                echo -e "${RED}❌ Server stopped unexpectedly${NC}"
                break
            fi
            sleep 10
        done
    else
        echo -e "${RED}❌ Failed to start server${NC}"
        echo -e "${YELLOW}📋 Check /tmp/ghostface.log for details${NC}"
        exit 1
    fi
}

# Run main function
main
