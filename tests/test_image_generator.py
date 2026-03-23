"""Tests for the Image Generator Lambda."""

import os

import boto3
import pytest
from moto import mock_aws

from image_generator.image_prompts import get_image_prompt


class TestImagePrompts:
    """Test base image prompt retrieval."""

    def test_known_type_returns_prompt(self):
        prompt = get_image_prompt("YOUR_POST_TYPE_1")
        assert len(prompt) > 0
        assert "No text" in prompt

    def test_unknown_type_returns_fallback(self):
        prompt = get_image_prompt("nonexistent-type")
        assert len(prompt) > 0
        assert "No text" in prompt


class TestS3Upload:
    """Test S3 upload functionality."""

    @mock_aws
    def test_upload_to_s3(self):
        os.environ["IMAGE_BUCKET"] = "test-bucket"
        os.environ["OPENAI_SECRET_ARN"] = "test"
        os.environ["FONTS_DIR"] = "/tmp"

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-bucket")

        from image_generator.handler import upload_to_s3

        key = upload_to_s3(b"fake-image-data", "images/2025-01-01/01-test.jpg")
        assert key == "images/2025-01-01/01-test.jpg"

        obj = s3.get_object(Bucket="test-bucket", Key=key)
        assert obj["Body"].read() == b"fake-image-data"
