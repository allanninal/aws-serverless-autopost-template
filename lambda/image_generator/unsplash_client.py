"""Unsplash API client for fetching stock photos.

Using Unsplash for some posts saves cost on AI image generation while
still providing high-quality visuals. The Unsplash API is free for
up to 50 requests/hour.

Customize UNSPLASH_QUERIES to match your post types and content themes.
"""

import logging
import random

import requests

logger = logging.getLogger(__name__)

UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"

# ============================================================================
# CUSTOMIZE: Add search queries for each post type that uses Unsplash.
# Multiple queries per type ensures variety across days.
# ============================================================================
UNSPLASH_QUERIES = {
    "YOUR_POST_TYPE_2": [
        "YOUR_SEARCH_QUERY_1",
        "YOUR_SEARCH_QUERY_2",
        "YOUR_SEARCH_QUERY_3",
        "YOUR_SEARCH_QUERY_4",
        "YOUR_SEARCH_QUERY_5",
    ],
    # Add more post types as needed:
    # "your-other-type": [
    #     "query for variety 1",
    #     "query for variety 2",
    # ],
}


def fetch_unsplash_photo(post_type: str, access_key: str) -> bytes:
    """Fetch a random stock photo from Unsplash for the given post type.

    Picks a random query from the post type's query list, fetches a random
    page (1-5), and selects a random photo from the results. Triggers the
    Unsplash download endpoint for API compliance.

    Returns the raw image bytes.
    """
    queries = UNSPLASH_QUERIES.get(post_type)
    if not queries:
        raise ValueError(f"No Unsplash queries defined for post type: {post_type}")

    query = random.choice(queries)
    page = random.randint(1, 5)

    logger.info(f"Searching Unsplash: query='{query}', page={page}")

    # Search for photos
    search_response = requests.get(
        UNSPLASH_API_URL,
        params={
            "query": query,
            "page": page,
            "per_page": 30,
            "orientation": "landscape",
        },
        headers={"Authorization": f"Client-ID {access_key}"},
        timeout=15,
    )
    search_response.raise_for_status()
    results = search_response.json().get("results", [])

    if not results:
        raise RuntimeError(f"No Unsplash results for query='{query}', page={page}")

    photo = random.choice(results)
    photo_id = photo["id"]
    download_location = photo["links"]["download_location"]

    # Trigger download endpoint (Unsplash API guidelines requirement)
    requests.get(
        download_location,
        headers={"Authorization": f"Client-ID {access_key}"},
        timeout=10,
    )

    # Download the actual image (regular size ~1080px wide)
    image_url = photo["urls"]["regular"]
    logger.info(f"Downloading Unsplash photo {photo_id}: {image_url[:80]}...")

    image_response = requests.get(image_url, timeout=30)
    image_response.raise_for_status()

    logger.info(f"Downloaded {len(image_response.content):,} bytes from Unsplash")
    return image_response.content
