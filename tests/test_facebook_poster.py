"""Tests for the Facebook Poster Lambda and client."""

from unittest.mock import MagicMock, patch

import pytest

from facebook_poster.facebook_client import FacebookClient, FacebookClientError


class TestFacebookClient:
    """Test Facebook Graph API client."""

    @patch("facebook_poster.facebook_client.requests.get")
    def test_get_page_id(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "123456789"},
        )
        mock_get.return_value.raise_for_status = MagicMock()

        client = FacebookClient("test-token")
        page_id = client.get_page_id()
        assert page_id == "123456789"

    @patch("facebook_poster.facebook_client.requests.get")
    def test_page_id_is_cached(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "123456789"},
        )
        mock_get.return_value.raise_for_status = MagicMock()

        client = FacebookClient("test-token")
        client.get_page_id()
        client.get_page_id()
        assert mock_get.call_count == 1

    @patch("facebook_poster.facebook_client.requests.post")
    @patch("facebook_poster.facebook_client.requests.get")
    def test_post_photo_success(self, mock_get, mock_post):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "123456789"},
        )
        mock_get.return_value.raise_for_status = MagicMock()

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "photo_123", "post_id": "post_456"},
        )

        client = FacebookClient("test-token")
        result = client.post_photo(b"fake-image", "Test caption")
        assert result["id"] == "photo_123"

    @patch("facebook_poster.facebook_client.requests.post")
    @patch("facebook_poster.facebook_client.requests.get")
    def test_expired_token_raises_immediately(self, mock_get, mock_post):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "123456789"},
        )
        mock_get.return_value.raise_for_status = MagicMock()

        mock_post.return_value = MagicMock(
            status_code=400,
            json=lambda: {"error": {"code": 190, "message": "Token expired"}},
        )

        client = FacebookClient("test-token")
        with pytest.raises(FacebookClientError, match="token expired"):
            client.post_photo(b"fake-image", "Test caption")

    @patch("facebook_poster.facebook_client.requests.post")
    @patch("facebook_poster.facebook_client.requests.get")
    def test_duplicate_raises_immediately(self, mock_get, mock_post):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "123456789"},
        )
        mock_get.return_value.raise_for_status = MagicMock()

        mock_post.return_value = MagicMock(
            status_code=400,
            json=lambda: {"error": {"code": 506, "message": "Duplicate"}},
        )

        client = FacebookClient("test-token")
        with pytest.raises(FacebookClientError, match="Duplicate"):
            client.post_photo(b"fake-image", "Test caption")
