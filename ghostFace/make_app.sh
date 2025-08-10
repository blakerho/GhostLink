#!/bin/bash

echo "🎨 Creating GhostFace macOS Application..."
echo "=========================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the app name and path
APP_NAME="GhostFace"
APP_PATH="$SCRIPT_DIR/$APP_NAME.app"

# Remove existing app if it exists
if [ -d "$APP_PATH" ]; then
    echo "🗑️  Removing existing app..."
    rm -rf "$APP_PATH"
fi

# Compile the AppleScript into an application
echo "🔨 Compiling AppleScript to application..."
osacompile -o "$APP_PATH" "$SCRIPT_DIR/GhostFace.applescript"

if [ $? -eq 0 ]; then
    echo "✅ Successfully created $APP_NAME.app"
    echo ""
    echo "📋 Next steps:"
    echo "1. Double-click $APP_NAME.app to launch GhostFace"
    echo "2. The app will automatically:"
    echo "   - Start the Python web server"
    echo "   - Open your browser to http://localhost:5001"
    echo "   - Show notifications when ready"
    echo ""
    echo "🎉 You can now drag $APP_NAME.app to your Applications folder or Dock!"
    
    # Make the app executable
    chmod +x "$APP_PATH/Contents/MacOS/applet"
    
    echo ""
    echo "🚀 Try double-clicking $APP_NAME.app now!"
else
    echo "❌ Failed to create application"
    exit 1
fi
