"""Generate the BretClip straight razor icon."""

from PIL import Image, ImageDraw
import os


def create_razor_icon(size: int) -> Image.Image:
    """Create a modern straight razor icon at the specified size.

    Uses 4x supersampling for crisp anti-aliased edges.
    Modern semi-flat design with clean geometry.
    """
    # Render at 4x for supersampling
    render_size = size * 4
    img = Image.new('RGBA', (render_size, render_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    s = render_size / 256

    # === SHADOW (subtle depth) ===
    shadow_offset = int(4 * s)
    shadow_blade = [
        (int(55 * s) + shadow_offset, int(175 * s) + shadow_offset),
        (int(48 * s) + shadow_offset, int(100 * s) + shadow_offset),
        (int(65 * s) + shadow_offset, int(42 * s) + shadow_offset),
        (int(82 * s) + shadow_offset, int(52 * s) + shadow_offset),
        (int(72 * s) + shadow_offset, int(165 * s) + shadow_offset),
    ]
    draw.polygon(shadow_blade, fill=(0, 0, 0, 40))

    shadow_handle = [
        (int(58 * s) + shadow_offset, int(178 * s) + shadow_offset),
        (int(82 * s) + shadow_offset, int(182 * s) + shadow_offset),
        (int(195 * s) + shadow_offset, int(212 * s) + shadow_offset),
        (int(210 * s) + shadow_offset, int(220 * s) + shadow_offset),
        (int(205 * s) + shadow_offset, int(232 * s) + shadow_offset),
        (int(185 * s) + shadow_offset, int(226 * s) + shadow_offset),
        (int(55 * s) + shadow_offset, int(196 * s) + shadow_offset),
    ]
    draw.polygon(shadow_handle, fill=(0, 0, 0, 30))

    # === HANDLE (dark material) ===
    handle_color = (42, 42, 46, 255)         # #2a2a2e
    handle_outline = (56, 56, 60, 255)       # #38383c

    handle_points = [
        (int(58 * s), int(178 * s)),
        (int(82 * s), int(182 * s)),
        (int(195 * s), int(212 * s)),
        (int(210 * s), int(220 * s)),
        (int(205 * s), int(232 * s)),
        (int(185 * s), int(226 * s)),
        (int(55 * s), int(196 * s)),
    ]
    draw.polygon(handle_points, fill=handle_color, outline=handle_outline)

    # Handle accent lines (subtle groove detail)
    groove_color = (54, 54, 57, 255)
    for i in range(3):
        offset = int(10 * s * i)
        draw.line([
            (int((88 + offset) * s), int((187 + offset * 0.3) * s)),
            (int((185 + offset * 0.3) * s), int((216 + offset * 0.3) * s)),
        ], fill=groove_color, width=max(1, int(1.5 * s)))

    # === BLADE (clean steel) ===
    blade_light = (210, 218, 226, 255)       # Light steel
    blade_outline = (140, 150, 165, 255)     # Steel edge

    blade_points = [
        (int(55 * s), int(175 * s)),
        (int(48 * s), int(100 * s)),
        (int(65 * s), int(42 * s)),          # Blade tip
        (int(82 * s), int(52 * s)),
        (int(72 * s), int(165 * s)),
    ]
    draw.polygon(blade_points, fill=blade_light, outline=blade_outline)

    # Blade highlight (reflection stripe)
    highlight = (235, 240, 245, 255)
    highlight_points = [
        (int(52 * s), int(140 * s)),
        (int(50 * s), int(95 * s)),
        (int(58 * s), int(55 * s)),
        (int(63 * s), int(58 * s)),
        (int(56 * s), int(105 * s)),
        (int(58 * s), int(145 * s)),
    ]
    draw.polygon(highlight_points, fill=highlight)

    # Sharp edge line (cutting edge)
    edge_color = (90, 100, 115, 255)
    draw.line([
        (int(65 * s), int(42 * s)),
        (int(82 * s), int(52 * s)),
        (int(72 * s), int(165 * s)),
    ], fill=edge_color, width=max(1, int(2 * s)))

    # === PIVOT PIN (accent blue) ===
    pivot_color = (45, 127, 249, 255)        # #2d7ff9 - accent blue
    pivot_highlight = (74, 148, 255, 255)    # Lighter accent
    pivot_center = (int(65 * s), int(180 * s))
    pivot_radius = int(11 * s)

    draw.ellipse([
        pivot_center[0] - pivot_radius,
        pivot_center[1] - pivot_radius,
        pivot_center[0] + pivot_radius,
        pivot_center[1] + pivot_radius
    ], fill=pivot_color, outline=(30, 100, 220, 255))

    # Pivot highlight dot
    inner_r = int(4 * s)
    draw.ellipse([
        pivot_center[0] - inner_r,
        pivot_center[1] - inner_r - int(2 * s),
        pivot_center[0] + inner_r,
        pivot_center[1] + inner_r - int(2 * s)
    ], fill=pivot_highlight)

    # === DOWNSCALE with LANCZOS ===
    img = img.resize((size, size), Image.LANCZOS)

    return img


def create_multi_size_icon(output_path: str):
    """Create an ICO file with multiple sizes."""
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = create_razor_icon(size)
        images.append(img)

    # Save as ICO
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )

    print(f"Icon saved to: {output_path}")

    # Also save PNG versions for reference
    png_dir = os.path.dirname(output_path)
    for size, img in zip(sizes, images):
        png_path = os.path.join(png_dir, f"icon_{size}.png")
        img.save(png_path)
        print(f"PNG saved: {png_path}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "icon.ico")
    create_multi_size_icon(icon_path)
