#!/usr/bin/env python3
"""Generate a sample post locally without any API keys.

Creates a sample image with overlay text to preview how your posts
will look. No external API calls are made.

Usage:
    python scripts/generate_sample.py
    python scripts/generate_sample.py --style gradient
"""

import argparse
import io
import os
import sys

# Add lambda directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda", "image_generator"))

from PIL import Image

from overlay import apply_text_overlay


def create_placeholder_image(width: int = 1536, height: int = 1024) -> bytes:
    """Create a gradient placeholder image."""
    img = Image.new("RGB", (width, height))
    for y in range(height):
        for x in range(width):
            r = int(255 * (x / width))
            g = int(180 * (y / height))
            b = int(200 * (1 - x / width))
            img.putpixel((x, y), (r, g, b))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def main():
    parser = argparse.ArgumentParser(description="Generate a sample autopost image")
    parser.add_argument(
        "--style",
        choices=["panel", "gradient"],
        default="panel",
        help="Overlay style (default: panel)",
    )
    parser.add_argument(
        "--output",
        default="samples/sample_post.jpg",
        help="Output file path (default: samples/sample_post.jpg)",
    )
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Create placeholder image (portrait for gradient, landscape for panel)
    if args.style == "gradient":
        raw_bytes = create_placeholder_image(1024, 1536)
    else:
        raw_bytes = create_placeholder_image(1536, 1024)

    # Apply overlay
    result = apply_text_overlay(
        raw_bytes,
        main_text="Your Headline\nGoes Here",
        subtitle_text="YOUR_BRAND_NAME",
        watermark="FB: @YourPageName",
        fonts_dir=os.path.join(os.path.dirname(__file__), "..", "fonts"),
        style=args.style,
    )

    with open(args.output, "wb") as f:
        f.write(result)

    print(f"Sample image saved to: {args.output}")
    print(f"Style: {args.style}")
    size = "1080x1080" if args.style == "panel" else "1080x1350"
    print(f"Dimensions: {size}")


if __name__ == "__main__":
    main()
