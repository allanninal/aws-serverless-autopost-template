"""Post schedule configuration.

Customize this file to define your posting schedule. Each entry represents
one automated post per day. The scheduler will create one EventBridge
cron rule per entry.

Fields:
    post_number:  Unique integer ID (used in dedup key and S3 path)
    post_type:    Slug identifier (used in prompts, image styles, S3 path)
    local_time:   Display-only — the time in YOUR timezone
    display_name: Human-readable label (used in logs and dashboards)
    image_source: "openai" (AI-generated) or "unsplash" (stock photo)
"""

POST_SCHEDULE = [
    {
        "post_number": 1,
        "post_type": "YOUR_POST_TYPE_1",
        "local_time": "6:00 AM",
        "display_name": "Your Morning Post",
        "image_source": "openai",
    },
    {
        "post_number": 2,
        "post_type": "YOUR_POST_TYPE_2",
        "local_time": "12:00 PM",
        "display_name": "Your Midday Post",
        "image_source": "unsplash",
    },
    {
        "post_number": 3,
        "post_type": "YOUR_POST_TYPE_3",
        "local_time": "6:00 PM",
        "display_name": "Your Evening Post",
        "image_source": "openai",
    },
]
