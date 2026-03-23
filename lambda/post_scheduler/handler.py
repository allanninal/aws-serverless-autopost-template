"""Post Scheduler -- Orchestrator Lambda triggered by EventBridge.

This is the entry point for the autopost pipeline. EventBridge fires a cron
rule which invokes this function with {post_number, post_type}. The scheduler
then chains three downstream Lambdas synchronously:

    1. Content Generator  -> caption + image headline + image prompt
    2. Image Generator    -> AI image + Pillow overlay -> S3
    3. Facebook Poster    -> Graph API upload + DynamoDB dedup record
"""

import json
import logging
import os
from datetime import date, datetime, timedelta, timezone

import boto3

from config import POST_SCHEDULE

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client("lambda")
dynamodb = boto3.resource("dynamodb")

CONTENT_GENERATOR_FUNCTION = os.environ["CONTENT_GENERATOR_FUNCTION"]
IMAGE_GENERATOR_FUNCTION = os.environ["IMAGE_GENERATOR_FUNCTION"]
FACEBOOK_POSTER_FUNCTION = os.environ["FACEBOOK_POSTER_FUNCTION"]
DYNAMODB_TABLE_NAME = os.environ["DYNAMODB_TABLE_NAME"]

# Timezone offset from UTC (e.g. 8 for UTC+8, -5 for EST)
TIMEZONE_OFFSET = int(os.environ.get("TIMEZONE_OFFSET_HOURS", "0"))


def get_local_date() -> date:
    """Get today's date in your configured timezone."""
    tz = timezone(timedelta(hours=TIMEZONE_OFFSET))
    return datetime.now(tz).date()


def invoke_lambda(function_name: str, payload: dict) -> dict:
    """Invoke a Lambda function synchronously and return its response."""
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )
    response_payload = json.loads(response["Payload"].read())

    if response.get("FunctionError"):
        raise RuntimeError(f"Lambda {function_name} failed: {response_payload}")

    return response_payload


def is_already_posted(post_key: str) -> bool:
    """Check if this post was already published today (idempotency guard)."""
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    response = table.get_item(Key={"post_key": post_key})
    return "Item" in response


def lambda_handler(event, context):
    """Main handler -- orchestrates content generation, image creation, and posting."""
    post_number = event.get("post_number")
    post_type = event.get("post_type")

    if not post_number or not post_type:
        raise ValueError(f"Missing post_number or post_type in event: {event}")

    today = get_local_date()
    post_key = f"{today.isoformat()}-{post_number:02d}-{post_type}"

    logger.info(f"Processing post #{post_number} ({post_type}) for {today}")

    # Dedup check -- skip if already posted today
    if is_already_posted(post_key):
        logger.info(f"Post {post_key} already exists, skipping")
        return {"statusCode": 200, "body": f"Already posted: {post_key}"}

    # Look up post config for image source
    post_config = None
    for p in POST_SCHEDULE:
        if p["post_number"] == post_number:
            post_config = p
            break

    if not post_config:
        raise ValueError(f"Unknown post_number: {post_number}")

    image_source = post_config.get("image_source", "openai")
    logger.info(f"Image source: {image_source}")

    # Step 1: Generate content (caption + image headline + image prompt)
    logger.info("Invoking content generator...")
    content_result = invoke_lambda(CONTENT_GENERATOR_FUNCTION, {
        "post_number": post_number,
        "post_type": post_type,
        "date": today.isoformat(),
        "image_source": image_source,
    })

    caption = content_result.get("caption", "")
    image_text = content_result.get("image_text", "")
    image_subtitle = content_result.get("image_subtitle", "")
    image_prompt = content_result.get("image_prompt", "")

    if not caption:
        raise RuntimeError(f"Content generator returned empty caption for {post_type}")

    # Step 2: Generate image (AI or stock photo + Pillow overlay -> S3)
    logger.info("Invoking image generator...")
    image_result = invoke_lambda(IMAGE_GENERATOR_FUNCTION, {
        "post_number": post_number,
        "post_type": post_type,
        "date": today.isoformat(),
        "image_text": image_text,
        "image_subtitle": image_subtitle,
        "image_prompt": image_prompt,
        "image_source": image_source,
    })

    s3_key = image_result.get("s3_key", "")
    if not s3_key:
        raise RuntimeError(f"Image generator returned no s3_key for {post_type}")

    # Step 3: Post to Facebook (Graph API upload + DynamoDB record)
    logger.info("Invoking Facebook poster...")
    post_result = invoke_lambda(FACEBOOK_POSTER_FUNCTION, {
        "post_key": post_key,
        "post_number": post_number,
        "post_type": post_type,
        "date": today.isoformat(),
        "caption": caption,
        "s3_key": s3_key,
    })

    logger.info(f"Successfully posted {post_key}: {post_result}")
    return {
        "statusCode": 200,
        "body": {
            "post_key": post_key,
            "facebook_post_id": post_result.get("post_id"),
        },
    }
