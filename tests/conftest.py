"""Shared test fixtures for the autopost pipeline."""

import json
import os

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def mock_dynamodb(aws_credentials):
    """Create a mock DynamoDB table for testing."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-posted-content",
            KeySchema=[{"AttributeName": "post_key", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "post_key", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.meta.client.get_waiter("table_exists").wait(TableName="test-posted-content")
        yield table


@pytest.fixture
def mock_s3(aws_credentials):
    """Create a mock S3 bucket for testing."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-image-bucket")
        yield s3


@pytest.fixture
def mock_secrets(aws_credentials):
    """Create mock secrets in Secrets Manager."""
    with mock_aws():
        client = boto3.client("secretsmanager", region_name="us-east-1")

        # Create test secrets
        secrets = {
            "test/facebook": json.dumps({"page_access_token": "test-token"}),
            "test/openai": json.dumps({"api_key": "test-openai-key"}),
            "test/openrouter": json.dumps({"api_key": "test-openrouter-key"}),
            "test/unsplash": json.dumps({"access_key": "test-unsplash-key"}),
        }
        for name, value in secrets.items():
            client.create_secret(Name=name, SecretString=value)

        yield client


@pytest.fixture
def sample_event():
    """Return a sample EventBridge event for the post scheduler."""
    return {
        "post_number": 1,
        "post_type": "YOUR_POST_TYPE_1",
    }


@pytest.fixture
def sample_content_result():
    """Return a sample content generator response."""
    return {
        "caption": "This is a test caption for the Facebook post.",
        "image_text": "Test\nHeadline",
        "image_subtitle": "YOUR_BRAND_NAME",
        "image_prompt": "A beautiful sunset over the ocean with warm colors.",
    }
