#!/usr/bin/env python3
"""End-to-end local test for the autopost pipeline.

Runs the full pipeline locally: content generation -> image generation
-> optional Facebook posting. Requires API keys in environment or .env file.

Usage:
    # Dry run (no Facebook posting):
    python scripts/test_post_local.py --post-number 1

    # Full test with Facebook posting:
    python scripts/test_post_local.py --post-number 1 --post

    # With specific style:
    python scripts/test_post_local.py --post-number 1 --style gradient
"""

import argparse
import json
import os
import sys
from datetime import date

# Add lambda directories to path
for d in ["post_scheduler", "content_generator", "image_generator", "facebook_poster"]:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda", d))


def load_env():
    """Load environment variables from .env file if it exists."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


def main():
    parser = argparse.ArgumentParser(description="Test the autopost pipeline locally")
    parser.add_argument("--post-number", type=int, required=True, help="Post number to test")
    parser.add_argument("--post", action="store_true", help="Actually post to Facebook")
    parser.add_argument("--style", choices=["panel", "gradient"], default="panel")
    args = parser.parse_args()

    load_env()

    from config import POST_SCHEDULE

    post_config = None
    for p in POST_SCHEDULE:
        if p["post_number"] == args.post_number:
            post_config = p
            break

    if not post_config:
        print(f"Error: post_number {args.post_number} not found in POST_SCHEDULE")
        sys.exit(1)

    post_type = post_config["post_type"]
    today = date.today().isoformat()

    print(f"Testing post #{args.post_number} ({post_type}) for {today}")
    print(f"Image source: {post_config['image_source']}")
    print(f"Overlay style: {args.style}")
    print("-" * 60)

    # Step 1: Generate content
    print("\n[1/3] Generating content...")
    from handler import generate_content, strip_markdown, generate_image_headline

    raw = generate_content(post_type, today)
    caption = strip_markdown(raw)
    print(f"Caption ({len(caption)} chars):\n{caption}\n")

    headline = generate_image_headline(caption, post_type)
    print(f"Image headline: {headline}")

    # Step 2: Generate image
    print("\n[2/3] Generating image...")
    os.environ["OVERLAY_STYLE"] = args.style

    import io
    from PIL import Image

    if post_config["image_source"] == "openai":
        from image_generator.handler import generate_image
        raw_bytes = generate_image(f"A beautiful scene related to {post_type}")
    else:
        # Create placeholder for local testing
        img = Image.new("RGB", (1536, 1024), (100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        raw_bytes = buf.read()
        print("Using placeholder image (Unsplash requires API key)")

    from overlay import apply_text_overlay

    final_bytes = apply_text_overlay(
        raw_bytes,
        main_text=headline or "Test Headline",
        subtitle_text=post_config["display_name"],
        watermark=os.environ.get("WATERMARK_TEXT", "FB: @YourPage"),
        fonts_dir=os.path.join(os.path.dirname(__file__), "..", "fonts"),
        style=args.style,
    )

    os.makedirs("samples", exist_ok=True)
    output_path = f"samples/test_{post_type}.jpg"
    with open(output_path, "wb") as f:
        f.write(final_bytes)
    print(f"Image saved to: {output_path}")

    # Step 3: Post to Facebook (optional)
    if args.post:
        print("\n[3/3] Posting to Facebook...")
        from facebook_client import FacebookClient

        token = os.environ.get("FB_PAGE_ACCESS_TOKEN")
        if not token:
            print("Error: FB_PAGE_ACCESS_TOKEN not set")
            sys.exit(1)

        client = FacebookClient(token)
        result = client.post_photo(final_bytes, caption)
        print(f"Posted! Photo ID: {result.get('id')}")
    else:
        print("\n[3/3] Skipping Facebook post (use --post to enable)")

    print("\nDone!")


if __name__ == "__main__":
    main()
