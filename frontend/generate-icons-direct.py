#!/usr/bin/env python3
"""
Icon Generation Script - Direct Drawing for AnyLab Application

This script generates all required icon sizes by drawing the icon directly.
Requires: Pillow (PIL) - install with: pip install Pillow
"""

import os
import sys
import math
from pathlib import Path

try:
    from PIL import Image, ImageDraw
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

def create_gradient_image(size, start_color, end_color, vertical=True):
    """Create a gradient image."""
    width, height = size
    img = Image.new('RGB', size)
    pixels = img.load()
    
    if vertical:
        for y in range(height):
            ratio = y / height
            r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
            g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
            b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
            for x in range(width):
                pixels[x, y] = (r, g, b)
    else:
        for x in range(width):
            ratio = x / width
            r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
            g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
            b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
            for y in range(height):
                pixels[x, y] = (r, g, b)
    
    return img

def draw_hexagon(draw, center, radius, fill=None, outline=None, width=1):
    """Draw a hexagon with rounded corners."""
    x, y = center
    points = []
    for i in range(6):
        angle = math.pi / 3 * i
        px = x + radius * math.cos(angle)
        py = y + radius * math.sin(angle)
        points.append((px, py))
    
    if fill:
        draw.polygon(points, fill=fill, outline=None)
    if outline:
        # For outline, we'll draw lines with rounded ends
        for i in range(6):
            p1 = points[i]
            p2 = points[(i + 1) % 6]
            draw.line([p1, p2], fill=outline, width=width)

def create_icon(size):
    """Create the icon image."""
    width, height = size
    # Create white background
    img = Image.new('RGBA', size, (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Colors: green to match application styling (primary-700 to primary-500)
    green_dark = (21, 128, 61)  # #15803d (primary-700)
    green_light = (34, 197, 94)  # #22c55e (primary-500)
    
    center_x, center_y = width // 2, height // 2
    
    # Calculate sizes based on image dimensions
    # Hexagon should take up about 85% of the image
    hex_radius = int(min(width, height) * 0.42)
    hex_stroke_width = max(2, int(min(width, height) * 0.125))  # ~12.5% of size (much thicker)
    
    # Circle radius slightly larger for better visual balance
    circle_radius = int(min(width, height) * 0.15625)  # 1.25x bigger than stroke width (80/512 = 0.15625)
    
    # Circle centered in hexagon (at exact center)
    circle_center_y = center_y
    
    # Create gradient mask for hexagon outline
    # We'll draw the hexagon with gradient by creating a mask
    hex_mask = Image.new('L', size, 0)
    hex_draw = ImageDraw.Draw(hex_mask)
    
    # Draw hexagon outline on mask
    hex_points = []
    for i in range(6):
        angle = math.pi / 3 * i - math.pi / 6  # Rotate 30 degrees
        px = center_x + hex_radius * math.cos(angle)
        py = center_y + hex_radius * math.sin(angle)
        hex_points.append((px, py))
    
    # Draw hexagon outline with rounded corners
    for i in range(6):
        p1 = hex_points[i]
        p2 = hex_points[(i + 1) % 6]
        # Draw thick lines for the outline
        hex_draw.line([p1, p2], fill=255, width=hex_stroke_width)
        # Draw rounded corners
        hex_draw.ellipse([p1[0] - hex_stroke_width//2, p1[1] - hex_stroke_width//2,
                         p1[0] + hex_stroke_width//2, p1[1] + hex_stroke_width//2], fill=255)
    
    # Create gradient for hexagon
    hex_gradient = create_gradient_image(size, green_dark, green_light, vertical=True)
    hex_gradient.putalpha(hex_mask)
    
    # Composite hexagon gradient
    img = Image.alpha_composite(img, hex_gradient.convert('RGBA'))
    
    # Draw circle with gradient
    circle_mask = Image.new('L', size, 0)
    circle_draw = ImageDraw.Draw(circle_mask)
    circle_draw.ellipse([center_x - circle_radius, circle_center_y - circle_radius,
                        center_x + circle_radius, circle_center_y + circle_radius], fill=255)
    
    # Create gradient for circle
    circle_gradient = create_gradient_image(size, green_dark, green_light, vertical=True)
    circle_gradient.putalpha(circle_mask)
    
    # Composite circle gradient
    img = Image.alpha_composite(img, circle_gradient.convert('RGBA'))
    
    return img

def create_maskable_icon(image, size):
    """
    Create a maskable icon with safe zone.
    The safe zone is the center 80% of the icon.
    """
    safe_zone_ratio = 0.8
    safe_size = int(size[0] * safe_zone_ratio)
    
    # Create the icon at safe size
    safe_icon = create_icon((safe_size, safe_size))
    
    # Create a new image with the full size
    maskable = Image.new("RGBA", size, (255, 255, 255, 255))
    
    # Paste the safe icon in the center
    offset = ((size[0] - safe_size) // 2, (size[1] - safe_size) // 2)
    maskable.paste(safe_icon, offset)
    
    return maskable

def generate_icons(output_dir):
    """Generate all required icon sizes."""
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
                icon = create_maskable_icon(None, size)
                print(f"   ✓ {filename} ({size[0]}x{size[1]}) - maskable with safe zone")
            else:
                icon = create_icon(size)
                print(f"   ✓ {filename} ({size[0]}x{size[1]})")
            
            output_file = output_path / filename
            icon.save(output_file, "PNG", optimize=True)
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate ICO file for favicon
    try:
        favicon_32 = Image.open(output_path / "ai-favicon-32.png")
        ico_path = output_path / "ai-favicon.ico"
        favicon_32.save(ico_path, format="ICO", sizes=[(32, 32)])
        print(f"   ✓ ai-favicon.ico (32x32)")
        success_count += 1
    except Exception as e:
        print(f"   ⚠️  ai-favicon.ico: {e} (PNG favicon will be used)")
    
    # Also create ai-favicon.png (for index.html compatibility)
    try:
        favicon_32 = Image.open(output_path / "ai-favicon-32.png")
        favicon_path = output_path / "ai-favicon.png"
        favicon_32.save(favicon_path, "PNG")
        print(f"   ✓ ai-favicon.png (32x32)")
        success_count += 1
    except Exception as e:
        print(f"   ⚠️  ai-favicon.png: {e}")
    
    print("-" * 50)
    print(f"\n✅ Generated {success_count} icon files successfully!")
    
    return True

def main():
    """Main function."""
    print("🎨 AnyLab Icon Generator (Direct Drawing)")
    print("=" * 50)
    
    script_dir = Path(__file__).parent
    output_dir = script_dir / "public"
    
    # Generate icons
    success = generate_icons(output_dir)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()

