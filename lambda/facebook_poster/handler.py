"""Facebook Poster Lambda -- posts image+text to Facebook via Graph API.

Downloads the generated image from S3, uploads it to the Facebook Page
via the Graph API photos endpoint, and records the successful post in
DynamoDB for deduplication.
"""

import json
import logging
import os
import time

import boto3

from facebook_client import FacebookClient, FacebookClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets_client = boto3.client("secretsmanager")
s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

FACEBOOK_SECRET_ARN = os.environ.get("FACEBOOK_SECRET_ARN", "")
IMAGE_BUCKET = os.environ.get("IMAGE_BUCKET", "")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "")

_facebook_client = None


def get_facebook_client() -> FacebookClient:
    """Get FacebookClient with credentials from Secrets Manager (cached)."""
    global _facebook_client
    if _facebook_client is None:
        response = secrets_client.get_secret_value(SecretId=FACEBOOK_SECRET_ARN)
        secret = json.loads(response["SecretString"])
        _facebook_client = FacebookClient(secret["page_access_token"])
    return _facebook_client


def download_image_from_s3(s3_key: str) -> bytes:
    """Download an image from S3."""
    response = s3_client.get_object(Bucket=IMAGE_BUCKET, Key=s3_key)
    return response["Body"].read()


def record_post(post_key: str, post_data: dict) -> None:
    """Record a successful post in DynamoDB with 90-day TTL."""
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    ttl = int(time.time()) + (90 * 24 * 60 * 60)
    table.put_item(
        Item={
            "post_key": post_key,
            "post_id": post_data.get("id", ""),
            "post_type": post_data.get("post_type", ""),
            "date": post_data.get("date", ""),
            "posted_at": int(time.time()),
            "ttl": ttl,
        }
    )


def lambda_handler(event, context):
    """Post image+caption to Facebook and record in DynamoDB."""
    post_key = event["post_key"]
    post_type = event["post_type"]
    date_str = event["date"]
    caption = event["caption"]
    s3_key = event["s3_key"]

    logger.info(f"Posting {post_key} to Facebook")

    # Download image from S3
    image_data = download_image_from_s3(s3_key)
    logger.info(f"Downloaded image: {len(image_data)} bytes from {s3_key}")

    # Post to Facebook
    client = get_facebook_client()
    result = client.post_photo(image_data, caption)

    # Record in DynamoDB
    record_post(post_key, {
        "id": result.get("id", ""),
        "post_type": post_type,
        "date": date_str,
    })

    logger.info(f"Successfully posted {post_key}: photo_id={result.get('id')}")

    return {
        "post_id": result.get("id"),
        "post_key": post_key,
    }
