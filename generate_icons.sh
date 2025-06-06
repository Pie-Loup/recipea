#!/bin/bash

# Script to generate all required icon sizes from logo.svg
# Make sure ImageMagick is installed: brew install imagemagick

echo "🎨 Generating icons from logo.svg..."

# Create icons directory if it doesn't exist
mkdir -p app/static/icons

# Source SVG file
svg_file="app/static/logo.svg"

# Check if source file exists
if [ ! -f "$svg_file" ]; then
    echo "❌ Error: $svg_file not found!"
    exit 1
fi

# Define all the sizes needed based on your HTML and manifest.json
sizes=(16 32 57 60 72 76 96 114 120 128 144 152 180 192 384 512)

# Generate PNG icons for each size
for size in "${sizes[@]}"; do
    echo "📱 Generating ${size}x${size} icon..."
    magick "$svg_file" -resize "${size}x${size}" -background none "app/static/icons/icon-${size}x${size}.png"
    
    # Check if the file was created successfully
    if [ -f "app/static/icons/icon-${size}x${size}.png" ]; then
        echo "✅ Generated icon-${size}x${size}.png"
    else
        echo "❌ Failed to generate icon-${size}x${size}.png"
    fi
done

# Generate additional favicon sizes
echo "🔗 Generating favicon-32x32.png..."
magick "$svg_file" -resize "32x32" -background none "app/static/favicon-32x32.png"

echo "🍎 Generating apple-touch-icon.png (180x180)..."
magick "$svg_file" -resize "180x180" -background none "app/static/apple-touch-icon.png"

# Generate android-chrome versions (for PWA manifest compatibility)
echo "🤖 Generating android-chrome-192x192.png..."
cp "app/static/icons/icon-192x192.png" "app/static/android-chrome-192x192.png"

echo "🤖 Generating android-chrome-512x512.png..."
cp "app/static/icons/icon-512x512.png" "app/static/android-chrome-512x512.png"

# Generate a standard favicon.ico (16x16 and 32x32 combined)
echo "🔗 Generating favicon.ico..."
magick "$svg_file" -resize "16x16" -background none temp16.png
magick "$svg_file" -resize "32x32" -background none temp32.png
magick temp16.png temp32.png app/static/favicon.ico
rm temp16.png temp32.png

echo ""
echo "🎉 All icons generated successfully!"
echo "📁 Generated files:"
echo "   - app/static/icons/icon-{16,32,57,60,72,76,96,114,120,128,144,152,180,192,384,512}x{size}.png"
echo "   - app/static/favicon-32x32.png"
echo "   - app/static/apple-touch-icon.png"
echo "   - app/static/favicon.ico"
echo "   - app/static/android-chrome-{192x192,512x512}.png"
echo ""
echo "🔍 To verify all icons were created:"
echo "   ls -la app/static/icons/"
echo "   ls -la app/static/favicon* app/static/apple-touch-icon.png"
