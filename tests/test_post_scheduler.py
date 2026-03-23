"""Tests for the Post Scheduler (orchestrator) Lambda."""

import json
import os
from datetime import date
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws


class TestPostSchedulerConfig:
    """Test schedule configuration validation."""

    def test_schedule_has_unique_post_numbers(self):
        from post_scheduler.config import POST_SCHEDULE

        numbers = [p["post_number"] for p in POST_SCHEDULE]
        assert len(numbers) == len(set(numbers)), "Duplicate post numbers found"

    def test_schedule_has_unique_post_types(self):
        from post_scheduler.config import POST_SCHEDULE

        types = [p["post_type"] for p in POST_SCHEDULE]
        assert len(types) == len(set(types)), "Duplicate post types found"

    def test_schedule_entries_have_required_fields(self):
        from post_scheduler.config import POST_SCHEDULE

        required = {"post_number", "post_type", "local_time", "display_name", "image_source"}
        for entry in POST_SCHEDULE:
            missing = required - set(entry.keys())
            assert not missing, f"Entry {entry.get('post_number')} missing fields: {missing}"

    def test_image_source_is_valid(self):
        from post_scheduler.config import POST_SCHEDULE

        valid = {"openai", "unsplash"}
        for entry in POST_SCHEDULE:
            assert entry["image_source"] in valid, (
                f"Invalid image_source '{entry['image_source']}' "
                f"for post #{entry['post_number']}"
            )


class TestDedupCheck:
    """Test deduplication logic."""

    @mock_aws
    def test_is_already_posted_returns_false_when_not_posted(self):
        os.environ["DYNAMODB_TABLE_NAME"] = "test-posted-content"
        os.environ["CONTENT_GENERATOR_FUNCTION"] = "test"
        os.environ["IMAGE_GENERATOR_FUNCTION"] = "test"
        os.environ["FACEBOOK_POSTER_FUNCTION"] = "test"

        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="test-posted-content",
            KeySchema=[{"AttributeName": "post_key", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "post_key", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        import importlib
        import post_scheduler.handler as handler_mod

        handler_mod.dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        assert handler_mod.is_already_posted("2025-01-01-01-test") is False

    @mock_aws
    def test_is_already_posted_returns_true_when_posted(self):
        os.environ["DYNAMODB_TABLE_NAME"] = "test-posted-content"
        os.environ["CONTENT_GENERATOR_FUNCTION"] = "test"
        os.environ["IMAGE_GENERATOR_FUNCTION"] = "test"
        os.environ["FACEBOOK_POSTER_FUNCTION"] = "test"

        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-posted-content",
            KeySchema=[{"AttributeName": "post_key", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "post_key", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.put_item(Item={"post_key": "2025-01-01-01-test"})

        import post_scheduler.handler as handler_mod

        handler_mod.dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        assert handler_mod.is_already_posted("2025-01-01-01-test") is True


class TestHandlerValidation:
    """Test handler input validation."""

    def test_missing_post_number_raises(self):
        os.environ["DYNAMODB_TABLE_NAME"] = "test"
        os.environ["CONTENT_GENERATOR_FUNCTION"] = "test"
        os.environ["IMAGE_GENERATOR_FUNCTION"] = "test"
        os.environ["FACEBOOK_POSTER_FUNCTION"] = "test"

        from post_scheduler.handler import lambda_handler

        with pytest.raises(ValueError, match="Missing post_number"):
            lambda_handler({"post_type": "test"}, None)

    def test_missing_post_type_raises(self):
        os.environ["DYNAMODB_TABLE_NAME"] = "test"
        os.environ["CONTENT_GENERATOR_FUNCTION"] = "test"
        os.environ["IMAGE_GENERATOR_FUNCTION"] = "test"
        os.environ["FACEBOOK_POSTER_FUNCTION"] = "test"

        from post_scheduler.handler import lambda_handler

        with pytest.raises(ValueError, match="Missing post_number"):
            lambda_handler({"post_number": 1}, None)
