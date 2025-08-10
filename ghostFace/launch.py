#!/usr/bin/env python3
"""
GhostFace Launcher
Simple script to launch the GhostFace web interface from anywhere
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Change to the ghostFace directory
    os.chdir(script_dir)
    
    print("👻 GhostFace Launcher")
    print("=" * 50)
    print(f"📁 Working directory: {script_dir}")
    print("🚀 Starting GhostFace web interface...")
    print("")
    
    try:
        # Check if Python is available
        subprocess.run([sys.executable, "--version"], check=True, capture_output=True)
        
        # Try to start the web interface
        subprocess.run([sys.executable, "start_ghostlink_web.py"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print("")
        print("Troubleshooting:")
        print("1. Make sure Python is installed and in your PATH")
        print("2. Make sure you're in the correct directory")
        print("3. Try running: python start_ghostlink_web.py manually")
        return 1
    except KeyboardInterrupt:
        print("\n👋 GhostFace stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
