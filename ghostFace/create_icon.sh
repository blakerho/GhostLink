#!/bin/bash

echo "🎨 Creating GhostFace Icon..."
echo "============================="

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "❌ ImageMagick not found. Installing..."
    if command -v brew &> /dev/null; then
        brew install imagemagick
    else
        echo "Please install ImageMagick first:"
        echo "brew install imagemagick"
        exit 1
    fi
fi

# Convert SVG to PNG (128x128)
echo "🔄 Converting SVG to PNG..."
convert ghost_icon.svg -resize 128x128 ghost_icon_128.png

# Create different sizes for macOS
echo "🔄 Creating different icon sizes..."
convert ghost_icon.svg -resize 16x16 ghost_icon_16.png
convert ghost_icon.svg -resize 32x32 ghost_icon_32.png
convert ghost_icon.svg -resize 64x64 ghost_icon_64.png
convert ghost_icon.svg -resize 256x256 ghost_icon_256.png
convert ghost_icon.svg -resize 512x512 ghost_icon_512.png

# Create ICNS file (macOS icon format)
echo "🔄 Creating ICNS file..."
mkdir ghost_icon.iconset
cp ghost_icon_16.png ghost_icon.iconset/icon_16x16.png
cp ghost_icon_32.png ghost_icon.iconset/icon_16x16@2x.png
cp ghost_icon_32.png ghost_icon.iconset/icon_32x32.png
cp ghost_icon_64.png ghost_icon.iconset/icon_32x32@2x.png
cp ghost_icon_128.png ghost_icon.iconset/icon_128x128.png
cp ghost_icon_256.png ghost_icon.iconset/icon_128x128@2x.png
cp ghost_icon_256.png ghost_icon.iconset/icon_256x256.png
cp ghost_icon_512.png ghost_icon.iconset/icon_256x256@2x.png

iconutil -c icns ghost_icon.iconset

# Clean up
rm -rf ghost_icon.iconset
rm ghost_icon_*.png

echo "✅ Icon created successfully!"
echo "📁 Files created:"
echo "   - ghost_icon.icns (macOS app icon)"
echo "   - ghost_icon.svg (source file)"
echo ""
echo "🎯 To use this icon in your Automator app:"
echo "1. Create your app in Automator"
echo "2. Right-click the app in Finder"
echo "3. Select 'Get Info'"
echo "4. Drag ghost_icon.icns to the icon area"
