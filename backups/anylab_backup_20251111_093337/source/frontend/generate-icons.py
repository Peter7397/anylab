#!/usr/bin/env python3
"""
Icon Generation Script for AnyLab Application

This script generates all required icon sizes from a source image.
Requires: Pillow (PIL) - install with: pip install Pillow
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("❌ Error: Pillow is not installed.")
    print("   Install it with: pip install Pillow")
    sys.exit(1)

# Icon sizes and filenames
ICON_CONFIG = [
    {"size": (32, 32), "filename": "ai-favicon-32.png"},
    {"size": (192, 192), "filename": "ai-logo-192.png"},
    {"size": (512, 512), "filename": "ai-logo-512.png"},
    {"size": (512, 512), "filename": "ai-maskable-512.png", "maskable": True},
]

# Source image paths to try (in order)
SOURCE_PATHS = [
    "public/icon-source.png",
    "public/icon-source.jpg",
    "public/icon-source.jpeg",
    "icon-source.png",
    "icon-source.jpg",
    "icon-source.jpeg",
]


def find_source_image():
    """Find the source icon image."""
    script_dir = Path(__file__).parent
    public_dir = script_dir / "public"
    
    # Try different source paths
    for source_path in SOURCE_PATHS:
        full_path = script_dir / source_path
        if full_path.exists():
            return full_path
    
    # List available images in public directory
    if public_dir.exists():
        images = list(public_dir.glob("*.png")) + list(public_dir.glob("*.jpg")) + list(public_dir.glob("*.jpeg"))
        if images:
            print(f"\n📁 Found these images in public/ directory:")
            for img in images:
                print(f"   - {img.name}")
            print(f"\n💡 Tip: Rename your source image to 'icon-source.png' for automatic detection")
    
    return None


def create_maskable_icon(image, size):
    """
    Create a maskable icon with safe zone.
    The safe zone is the center 80% of the icon.
    """
    # Create a new image with padding (safe zone)
    safe_zone_ratio = 0.8
    safe_size = int(size[0] * safe_zone_ratio)
    
    # Resize the original image to fit the safe zone
    resized = image.resize((safe_size, safe_size), Image.Resampling.LANCZOS)
    
    # Create a new image with the full size
    maskable = Image.new("RGBA", size, (0, 0, 0, 0))
    
    # Paste the resized image in the center
    offset = ((size[0] - safe_size) // 2, (size[1] - safe_size) // 2)
    maskable.paste(resized, offset)
    
    return maskable


def generate_icons(source_path, output_dir):
    """Generate all required icon sizes from source image."""
    print(f"\n🖼️  Loading source image: {source_path}")
    
    try:
        source_image = Image.open(source_path)
        print(f"   ✓ Image loaded: {source_image.size[0]}x{source_image.size[1]} pixels")
    except Exception as e:
        print(f"❌ Error loading image: {e}")
        return False
    
    # Convert to RGBA if needed
    if source_image.mode != "RGBA":
        source_image = source_image.convert("RGBA")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📦 Generating icons in: {output_dir}")
    print("-" * 50)
    
    success_count = 0
    
    for config in ICON_CONFIG:
        size = config["size"]
        filename = config["filename"]
        is_maskable = config.get("maskable", False)
        
        try:
            if is_maskable:
                icon = create_maskable_icon(source_image, size)
                print(f"   ✓ {filename} ({size[0]}x{size[1]}) - maskable with safe zone")
            else:
                icon = source_image.resize(size, Image.Resampling.LANCZOS)
                print(f"   ✓ {filename} ({size[0]}x{size[1]})")
            
            output_file = output_path / filename
            icon.save(output_file, "PNG", optimize=True)
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ {filename}: {e}")
    
    # Generate ICO file for favicon (optional, PNG works too)
    try:
        favicon_32 = Image.open(output_path / "ai-favicon-32.png")
        ico_path = output_path / "ai-favicon.ico"
        favicon_32.save(ico_path, format="ICO", sizes=[(32, 32)])
        print(f"   ✓ ai-favicon.ico (32x32)")
        success_count += 1
    except Exception as e:
        print(f"   ⚠️  ai-favicon.ico: {e} (PNG favicon will be used)")
    
    print("-" * 50)
    print(f"\n✅ Generated {success_count} icon files successfully!")
    print(f"\n📝 Next steps:")
    print(f"   1. Verify icons in {output_dir}")
    print(f"   2. Start your app: npm start")
    print(f"   3. Check browser tab and sidebar for your new icons")
    
    return True


def main():
    """Main function."""
    print("🎨 AnyLab Icon Generator")
    print("=" * 50)
    
    # Find source image
    source_path = find_source_image()
    
    if not source_path:
        print("\n❌ No source image found!")
        print("\n📋 Please:")
        print("   1. Place your icon image in frontend/public/icon-source.png")
        print("   2. Or specify the path as an argument:")
        print("      python3 generate-icons.py path/to/your/icon.png")
        sys.exit(1)
    
    # Get output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / "public"
    
    # Check if source was provided as argument
    if len(sys.argv) > 1:
        custom_source = Path(sys.argv[1])
        if custom_source.exists():
            source_path = custom_source
            print(f"\n📂 Using custom source: {source_path}")
        else:
            print(f"\n⚠️  Warning: Custom source not found: {custom_source}")
            print(f"   Using found source instead: {source_path}")
    
    # Generate icons
    success = generate_icons(source_path, output_dir)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()

