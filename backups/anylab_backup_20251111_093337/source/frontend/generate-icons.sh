#!/bin/bash
# Icon Generation Script for AnyLab Application (ImageMagick version)
# Requires: ImageMagick (install with: brew install imagemagick or apt-get install imagemagick)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUBLIC_DIR="$SCRIPT_DIR/public"

echo "🎨 AnyLab Icon Generator (ImageMagick)"
echo "========================================"

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "❌ Error: ImageMagick is not installed."
    echo "   Install it with:"
    echo "   - macOS: brew install imagemagick"
    echo "   - Ubuntu/Debian: sudo apt-get install imagemagick"
    echo "   - Or use the Python script: python3 generate-icons.py"
    exit 1
fi

# Find source image
SOURCE_IMAGE=""
for path in "$PUBLIC_DIR/icon-source.png" "$PUBLIC_DIR/icon-source.jpg" "$PUBLIC_DIR/icon-source.jpeg" \
            "$SCRIPT_DIR/icon-source.png" "$SCRIPT_DIR/icon-source.jpg" "$SCRIPT_DIR/icon-source.jpeg"; do
    if [ -f "$path" ]; then
        SOURCE_IMAGE="$path"
        break
    fi
done

# Check if source was provided as argument
if [ -n "$1" ] && [ -f "$1" ]; then
    SOURCE_IMAGE="$1"
fi

if [ -z "$SOURCE_IMAGE" ] || [ ! -f "$SOURCE_IMAGE" ]; then
    echo ""
    echo "❌ No source image found!"
    echo ""
    echo "📋 Please:"
    echo "   1. Place your icon image in frontend/public/icon-source.png"
    echo "   2. Or specify the path as an argument:"
    echo "      ./generate-icons.sh path/to/your/icon.png"
    exit 1
fi

echo ""
echo "🖼️  Source image: $SOURCE_IMAGE"
echo "📦 Output directory: $PUBLIC_DIR"
echo ""

# Create public directory if it doesn't exist
mkdir -p "$PUBLIC_DIR"

# Generate icons
echo "Generating icons..."
echo "-------------------"

# 32x32 favicon
convert "$SOURCE_IMAGE" -resize 32x32 "$PUBLIC_DIR/ai-favicon-32.png"
echo "   ✓ ai-favicon-32.png (32x32)"

# 192x192 app icon
convert "$SOURCE_IMAGE" -resize 192x192 "$PUBLIC_DIR/ai-logo-192.png"
echo "   ✓ ai-logo-192.png (192x192)"

# 512x512 app icon
convert "$SOURCE_IMAGE" -resize 512x512 "$PUBLIC_DIR/ai-logo-512.png"
echo "   ✓ ai-logo-512.png (512x512)"

# 512x512 maskable icon (with safe zone - center 80%)
# Create a canvas, resize image to 80% and center it
convert "$SOURCE_IMAGE" -resize 410x410 \
        -gravity center \
        -background transparent \
        -extent 512x512 \
        "$PUBLIC_DIR/ai-maskable-512.png"
echo "   ✓ ai-maskable-512.png (512x512, maskable)"

# Generate ICO file (optional)
convert "$PUBLIC_DIR/ai-favicon-32.png" "$PUBLIC_DIR/ai-favicon.ico"
echo "   ✓ ai-favicon.ico (32x32)"

echo "-------------------"
echo ""
echo "✅ All icons generated successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Verify icons in $PUBLIC_DIR"
echo "   2. Start your app: npm start"
echo "   3. Check browser tab and sidebar for your new icons"

