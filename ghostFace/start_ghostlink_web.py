#!/usr/bin/env python3
"""
GhostLink Web Interface Startup Script
Serves both the API backend and the web interface
"""

import os
import sys
from pathlib import Path

def check_flask_installed():
    """Check if Flask is installed"""
    try:
        import flask
        import flask_cors
        return True
    except ImportError:
        return False

def install_flask_dependencies():
    """Install Flask dependencies"""
    try:
        import subprocess
        requirements_path = Path(__file__).parent / "requirements_api.txt"
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path)
        ], capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error installing Flask: {e}")
        return False

def main():
    print("🚀 Starting GhostFace Web Interface...")
    print("📁 GhostLink path:", Path(__file__).parent.parent)
    
    # Check if Flask is installed
    if not check_flask_installed():
        print("⚠️  Flask not found. Installing dependencies...")
        if install_flask_dependencies():
            print("✅ Dependencies installed successfully!")
        else:
            print("❌ Failed to install dependencies automatically.")
            print("Please install manually with: pip install -r requirements_api.txt")
            return 1
    
    # Now import Flask and start the server
    try:
        from flask import Flask, send_from_directory
        from ghostlink_api import app as api_app
        
        # Use the API app directly and add web interface routes
        app = api_app
        
        # Serve the web interface
        @app.route('/')
        def serve_web_interface():
            return send_from_directory('.', 'GhostWeb.html')
        
        @app.route('/<path:filename>')
        def serve_static(filename):
            return send_from_directory('.', filename)
        
        print("🌐 Web interface: http://localhost:5001")
        print("🔌 API endpoint: http://localhost:5001/api")
        print("")
        print("To use the web interface:")
        print("1. Open http://localhost:5001 in your browser")
        print("2. If needed, install GhostLink and dependencies from the UI")
        print("3. Select your GhostLink directory")
        print("4. Choose your encoding/decoding options")
        print("5. Click the action buttons to process")
        print("")
        print("Press Ctrl+C to stop the server")
        
        app.run(debug=True, host='0.0.0.0', port=5001)
        
    except ImportError as e:
        print(f"❌ Error importing Flask modules: {e}")
        print("Please install dependencies with: pip install -r requirements_api.txt")
        return 1
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
