"""Content Generator Lambda -- generates Facebook post text via LLM API.

Makes 3 LLM calls per invocation:
    1. Generate the Facebook caption (main post text)
    2. Generate a catchy image headline (overlay text for the image)
    3. Generate an image prompt (for AI image generation)

Uses OpenRouter as the LLM gateway, defaulting to GPT-4.1-mini.
"""

import json
import logging
import os
import re

import boto3
import requests

from prompts import get_content_prompt, get_image_text

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets_client = boto3.client("secretsmanager")

OPENROUTER_SECRET_ARN = os.environ.get("OPENROUTER_SECRET_ARN", "")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4.1-mini")

_openrouter_key = None


def get_openrouter_key() -> str:
    """Retrieve OpenRouter API key from Secrets Manager (cached across invocations)."""
    global _openrouter_key
    if _openrouter_key is None:
        response = secrets_client.get_secret_value(SecretId=OPENROUTER_SECRET_ARN)
        secret = json.loads(response["SecretString"])
        _openrouter_key = secret["api_key"]
    return _openrouter_key


def generate_content(post_type: str, date_str: str) -> str:
    """Call LLM API via OpenRouter to generate post content."""
    prompt = get_content_prompt(post_type, date_str)

    headers = {
        "Authorization": f"Bearer {get_openrouter_key()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]},
        ],
        "max_tokens": 800,
        "temperature": 0.7,
    }

    response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"]
    return content.strip()


def strip_markdown(text: str) -> str:
    """Convert markdown to plain text for Facebook.

    LLMs sometimes return markdown formatting -- Facebook doesn't render it,
    so we strip it to avoid ugly asterisks and brackets in the post.
    """
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def generate_image_headline(caption: str, post_type: str) -> str:
    """Generate a catchy, striking headline from the post content for image overlay.

    The headline appears as bold text on the image -- it should capture the
    gist of the post so people scrolling get the message even without reading
    the full caption.
    """
    headers = {
        "Authorization": f"Bearer {get_openrouter_key()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You write catchy image headlines for a Facebook page.\n\n"
                    "Given a Facebook post, extract the CORE MESSAGE and turn it into a short, "
                    "punchy headline that stops someone scrolling.\n\n"
                    "RULES:\n"
                    "- Maximum 10 words total\n"
                    "- Use 2-3 short lines (separate with \\n)\n"
                    "- Each line should be 2-5 words\n"
                    "- No emojis, no hashtags\n"
                    "- Only periods, question marks, or ellipsis for punctuation\n"
                    "- No quotes around the text\n\n"
                    "Respond with ONLY the headline text, nothing else."
                ),
            },
            {
                "role": "user",
                "content": f"Post content:\n{caption}\n\nWrite a catchy image headline.",
            },
        ],
        "max_tokens": 50,
        "temperature": 0.7,
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        result = response.json()
        headline = result["choices"][0]["message"]["content"].strip()
        headline = headline.strip("\"'")
        return headline
    except Exception as e:
        logger.warning(f"Failed to generate image headline: {e}")
        return ""


def generate_image_prompt(caption: str, post_type: str) -> str:
    """Generate a content-driven image prompt based on the actual post text.

    The prompt follows OpenAI's recommended structure for gpt-image-1:
        1. Art style and medium
        2. Scene description
        3. Subject and focal point
        4. Lighting and mood
        5. Constraints (no text, no logos, etc.)
    """
    headers = {
        "Authorization": f"Bearer {get_openrouter_key()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert at writing image generation prompts.\n\n"
                    "Given a Facebook post, write a COMPLETE image generation prompt that depicts "
                    "the specific content of the post.\n\n"
                    "PROMPT STRUCTURE (follow this order):\n"
                    "1. Art style and medium\n"
                    "2. Scene and setting description\n"
                    "3. Subject -- expressive face, body language, emotional detail\n"
                    "4. Lighting, mood, and color palette\n"
                    "5. Constraints: No text, no words, no letters, no watermarks, no logos.\n\n"
                    "ENGAGEMENT RULES:\n"
                    "- FACES = +38% engagement -- always prioritize human faces with emotion\n"
                    "- HIGH CONTRAST stops the scroll -- bold colors, strong light-dark contrast\n"
                    "- THUMBNAIL TEST: One clear subject recognizable at 200x200px\n"
                    "- Avoid cluttered compositions -- one clear subject, one clear mood\n\n"
                    "Respond with ONLY the image prompt (3-5 sentences), nothing else."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Post type: {post_type}\n\n"
                    f"Post content:\n{caption}\n\n"
                    "Write a complete image generation prompt for this specific post."
                ),
            },
        ],
        "max_tokens": 400,
        "temperature": 0.75,
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"Failed to generate image prompt: {e}")
        return ""


def lambda_handler(event, context):
    """Generate content for a specific post type and date."""
    post_type = event["post_type"]
    post_number = event["post_number"]
    date_str = event["date"]

    logger.info(f"Generating content for {post_type} on {date_str}")

    # Generate the Facebook caption
    raw_content = generate_content(post_type, date_str)
    caption = strip_markdown(raw_content)

    # Generate catchy image headline from actual content
    image_headline = generate_image_headline(caption, post_type)
    if image_headline:
        logger.info(f"Image headline: {image_headline}")

    # Get static image overlay text (fallback if AI headline fails)
    image_text_data = get_image_text(post_type)
    final_image_text = image_headline if image_headline else image_text_data["main_text"]

    # Generate image prompt only for OpenAI posts (skip for Unsplash stock posts)
    image_source = event.get("image_source", "openai")
    image_prompt = ""
    if image_source == "openai":
        image_prompt = generate_image_prompt(caption, post_type)
        logger.info(f"Image prompt: {image_prompt[:100]}...")
    else:
        logger.info(f"Skipping image prompt generation (image_source={image_source})")

    logger.info(f"Generated {len(caption)} chars for {post_type}")

    return {
        "caption": caption,
        "image_text": final_image_text,
        "image_subtitle": image_text_data["subtitle"],
        "image_prompt": image_prompt,
    }
