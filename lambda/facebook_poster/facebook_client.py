"""Facebook Graph API client for posting photos with captions.

Production-grade client with:
    - Automatic Page ID discovery from access token
    - Exponential backoff retry for rate limits and transient errors
    - Error classification (fatal vs retryable)
    - Configurable Graph API version
"""

import logging
import os
import time

import requests

logger = logging.getLogger()

FACEBOOK_GRAPH_API_VERSION = os.environ.get("FB_GRAPH_API_VERSION", "v23.0")
FACEBOOK_GRAPH_API_BASE = f"https://graph.facebook.com/{FACEBOOK_GRAPH_API_VERSION}"


class FacebookClientError(Exception):
    """Raised when Facebook Graph API returns an error."""

    pass


class FacebookClient:
    def __init__(self, page_access_token: str):
        self.page_access_token = page_access_token
        self._page_id = None

    def get_page_id(self) -> str:
        """Get the Page ID associated with the access token (cached)."""
        if self._page_id is None:
            url = f"{FACEBOOK_GRAPH_API_BASE}/me"
            params = {"access_token": self.page_access_token, "fields": "id"}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            self._page_id = response.json()["id"]
        return self._page_id

    def post_photo(self, image_data: bytes, caption: str, max_retries: int = 3) -> dict:
        """Post a photo with caption to the Facebook Page.

        Retry strategy:
            - Rate limit (codes 4, 17, 32, 613): exponential backoff (10s, 20s, 40s)
            - Token expired (code 190): fail immediately (non-retryable)
            - Duplicate content (code 506): fail immediately
            - Network errors: exponential backoff (5s, 10s, 20s)

        Returns:
            dict with 'id' (photo ID) and 'post_id'
        """
        page_id = self.get_page_id()
        url = f"{FACEBOOK_GRAPH_API_BASE}/{page_id}/photos"

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    data={
                        "message": caption,
                        "access_token": self.page_access_token,
                    },
                    files={
                        "source": ("post.jpg", image_data, "image/jpeg"),
                    },
                    timeout=30,
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Posted photo to page {page_id}: {result}")
                    return result

                error_data = response.json().get("error", {})
                error_code = error_data.get("code", 0)
                error_msg = error_data.get("message", response.text)

                # Token expired -- cannot retry
                if error_code == 190:
                    raise FacebookClientError(
                        f"Page access token expired (error 190): {error_msg}"
                    )

                # Duplicate content
                if error_code == 506:
                    raise FacebookClientError(
                        f"Duplicate post detected (error 506): {error_msg}"
                    )

                # Rate limit or transient error -- retry with backoff
                if error_code in (4, 17, 32, 613):
                    wait_time = (2**attempt) * 10
                    logger.warning(
                        f"Rate limited (code {error_code}), "
                        f"retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    continue

                raise FacebookClientError(
                    f"Facebook API error (code {error_code}): {error_msg}"
                )

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2**attempt) * 5
                    logger.warning(
                        f"Request failed: {e}, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    raise FacebookClientError(
                        f"Request failed after {max_retries} attempts: {e}"
                    )

        raise FacebookClientError(f"Failed to post after {max_retries} attempts")
