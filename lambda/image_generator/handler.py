"""Image Generator Lambda -- AI image generation + Pillow text overlay.

Supports two image sources:
    - "openai":   Generate original images with gpt-image-1
    - "unsplash": Fetch stock photos from Unsplash API (free, saves cost)

Both sources go through the same Pillow overlay pipeline to add
headline text, subtitle, and watermark before uploading to S3.
"""

import base64
import json
import logging
import os

import boto3
from openai import OpenAI

from image_prompts import get_image_prompt
from overlay import apply_text_overlay
from unsplash_client import fetch_unsplash_photo

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets_client = boto3.client("secretsmanager")
s3_client = boto3.client("s3")

OPENAI_SECRET_ARN = os.environ.get("OPENAI_SECRET_ARN", "")
UNSPLASH_SECRET_ARN = os.environ.get("UNSPLASH_SECRET_ARN", "")
IMAGE_BUCKET = os.environ.get("IMAGE_BUCKET", "")
FONTS_DIR = os.environ.get("FONTS_DIR", "/var/task/fonts")
WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT", "YOUR_WATERMARK_TEXT")
OVERLAY_STYLE = os.environ.get("OVERLAY_STYLE", "panel")

_openai_client = None
_unsplash_key = None


def get_openai_client() -> OpenAI:
    """Get OpenAI client with API key from Secrets Manager (cached)."""
    global _openai_client
    if _openai_client is None:
        response = secrets_client.get_secret_value(SecretId=OPENAI_SECRET_ARN)
        secret = json.loads(response["SecretString"])
        _openai_client = OpenAI(api_key=secret["api_key"])
    return _openai_client


def get_unsplash_key() -> str:
    """Get Unsplash access key from Secrets Manager (cached)."""
    global _unsplash_key
    if _unsplash_key is None:
        response = secrets_client.get_secret_value(SecretId=UNSPLASH_SECRET_ARN)
        secret = json.loads(response["SecretString"])
        _unsplash_key = secret["access_key"]
    return _unsplash_key


def generate_image(prompt: str) -> bytes:
    """Generate an image using OpenAI gpt-image-1."""
    client = get_openai_client()

    # Portrait for gradient overlay, landscape for panel overlay
    size = "1024x1536" if OVERLAY_STYLE == "gradient" else "1536x1024"

    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=size,
        quality="medium",
        n=1,
    )

    image_data = base64.b64decode(result.data[0].b64_json)
    return image_data


def upload_to_s3(image_bytes: bytes, s3_key: str) -> str:
    """Upload image to S3 and return the key."""
    s3_client.put_object(
        Bucket=IMAGE_BUCKET,
        Key=s3_key,
        Body=image_bytes,
        ContentType="image/jpeg",
    )
    logger.info(f"Uploaded image to s3://{IMAGE_BUCKET}/{s3_key}")
    return s3_key


def lambda_handler(event, context):
    """Generate image, apply overlay, upload to S3."""
    post_type = event["post_type"]
    post_number = event["post_number"]
    date_str = event["date"]
    image_text = event.get("image_text", "")
    image_subtitle = event.get("image_subtitle", "")
    image_prompt = event.get("image_prompt", "")

    image_source = event.get("image_source", "openai")
    logger.info(f"Generating image for {post_type} on {date_str} (source: {image_source})")

    # Step 1: Get raw image bytes
    if image_source == "unsplash":
        try:
            access_key = get_unsplash_key()
            raw_image_bytes = fetch_unsplash_photo(post_type, access_key)
            logger.info(f"Fetched Unsplash photo: {len(raw_image_bytes)} bytes")
        except Exception as e:
            logger.warning(f"Unsplash failed, falling back to OpenAI: {e}")
            image_source = "openai"

    if image_source == "openai":
        if image_prompt:
            prompt = image_prompt
            logger.info(f"Using content-driven image prompt: {prompt[:100]}...")
        else:
            prompt = get_image_prompt(post_type)
            logger.info(f"Using base image prompt for {post_type}")

        raw_image_bytes = generate_image(prompt)
        logger.info(f"Generated OpenAI image: {len(raw_image_bytes)} bytes")

    # Step 2: Apply text overlay with Pillow
    final_image_bytes = apply_text_overlay(
        raw_image_bytes,
        main_text=image_text,
        subtitle_text=image_subtitle,
        watermark=WATERMARK_TEXT,
        fonts_dir=FONTS_DIR,
        style=OVERLAY_STYLE,
    )
    logger.info(f"Applied overlay ({OVERLAY_STYLE}): {len(final_image_bytes)} bytes")

    # Step 3: Upload to S3
    s3_key = f"images/{date_str}/{post_number:02d}-{post_type}.jpg"
    upload_to_s3(final_image_bytes, s3_key)

    return {
        "s3_key": s3_key,
        "bucket": IMAGE_BUCKET,
    }
