#!/usr/bin/env python3
"""
Icon Generation Script from SVG for AnyLab Application

This script generates all required icon sizes from an SVG source.
Requires: cairosvg - install with: pip install cairosvg
"""

import os
import sys
from pathlib import Path

try:
    import cairosvg
except ImportError:
    print("❌ Error: cairosvg is not installed.")
    print("   Install it with: pip install cairosvg")
    print("   Or use: pip3 install cairosvg")
    sys.exit(1)

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

def generate_icons_from_svg(svg_path, output_dir):
    """Generate all required icon sizes from SVG source."""
    print(f"\n🖼️  Loading SVG: {svg_path}")
    
    if not Path(svg_path).exists():
        print(f"❌ Error: SVG file not found: {svg_path}")
        return False
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📦 Generating icons in: {output_dir}")
    print("-" * 50)
    
    success_count = 0
    
    # First, render SVG to a high-res PNG (1024x1024) for best quality
    temp_png = output_path / "_temp_icon_1024.png"
    try:
        cairosvg.svg2png(url=str(svg_path), write_to=str(temp_png), output_width=1024, output_height=1024)
        source_image = Image.open(temp_png)
        print(f"   ✓ SVG rendered: {source_image.size[0]}x{source_image.size[1]} pixels")
    except Exception as e:
        print(f"❌ Error rendering SVG: {e}")
        return False
    
    # Convert to RGBA if needed
    if source_image.mode != "RGBA":
        source_image = source_image.convert("RGBA")
    
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
    
    # Generate ICO file for favicon
    try:
        favicon_32 = Image.open(output_path / "ai-favicon-32.png")
        ico_path = output_path / "ai-favicon.ico"
        favicon_32.save(ico_path, format="ICO", sizes=[(32, 32)])
        print(f"   ✓ ai-favicon.ico (32x32)")
        success_count += 1
    except Exception as e:
        print(f"   ⚠️  ai-favicon.ico: {e} (PNG favicon will be used)")
    
    # Clean up temp file
    try:
        temp_png.unlink()
    except:
        pass
    
    print("-" * 50)
    print(f"\n✅ Generated {success_count} icon files successfully!")
    
    return True

def main():
    """Main function."""
    print("🎨 AnyLab Icon Generator (from SVG)")
    print("=" * 50)
    
    script_dir = Path(__file__).parent
    svg_path = script_dir / "public" / "ai-icon.svg"
    
    # Check if custom SVG path provided
    if len(sys.argv) > 1:
        custom_svg = Path(sys.argv[1])
        if custom_svg.exists():
            svg_path = custom_svg
        else:
            print(f"\n⚠️  Warning: Custom SVG not found: {custom_svg}")
            print(f"   Using default: {svg_path}")
    
    if not svg_path.exists():
        print(f"\n❌ SVG file not found: {svg_path}")
        print("\n📋 Please ensure ai-icon.svg exists in frontend/public/")
        sys.exit(1)
    
    output_dir = script_dir / "public"
    
    # Generate icons
    success = generate_icons_from_svg(svg_path, output_dir)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()

