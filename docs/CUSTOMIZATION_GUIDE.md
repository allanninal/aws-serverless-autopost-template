# Customization Guide

This project is designed as a general-purpose framework. You define the **content type**, **prompts**, **image style**, and **schedule** -- the pipeline handles the rest.

> **New to this?** Start with the [Setup Guide](SETUP_GUIDE.md) to install tools and get your API keys first. Come back here once you're ready to customize the content.

## Key Concepts

Before diving in, here are a few terms you'll see:

- **Prompt** -- Instructions you give to an AI model. Think of it like a creative brief: you describe what you want, the AI generates it. For example, telling the AI "Write a motivational post about perseverance for young professionals" is a prompt.
- **Post type** -- A category of post on your schedule. Each type has its own prompt and image style. For example: `"morning-motivation"`, `"midday-tip"`, `"evening-quote"`.
- **Image source** -- Where the image comes from. Either `"openai"` (AI generates a unique image, ~$0.04-0.08 each) or `"unsplash"` (free stock photo from Unsplash).
- **Overlay style** -- How text appears on the image. `"panel"` puts text in a dark bar below the image (1080x1080 square). `"gradient"` fades the image to black and puts text on top (1080x1350 portrait).
- **Cron expression** -- A schedule format that tells AWS when to run your post. You specify the UTC hour and minute. The [Setup Guide](SETUP_GUIDE.md#step-6d-match-the-schedule-in-cdk) shows how to convert local time to UTC.

## Quick Start: 5 Steps to Customize

1. **Define your schedule** in `infra/stacks/autopost_stack.py` -- set `POST_SCHEDULE` with your post types and cron times.
2. **Write your prompts** in `lambda/content_generator/prompts.py` -- tell the AI what content to write for each post type.
3. **Configure image style** in `lambda/image_generator/image_prompts.py` -- describe the visual style for AI-generated images, or list Unsplash search keywords.
4. **Set your secrets** in AWS Secrets Manager -- Facebook Page token, OpenAI key, OpenRouter key, Unsplash key.
5. **Deploy** with `cdk deploy` -- your posts start running on schedule automatically.

---

## Example 1: Daily Motivational Quotes Page

**Use case:** A Facebook page that posts 3 inspirational quotes per day with beautiful AI-generated backgrounds.

### Files to change

| File | What to change |
|---|---|
| `infra/stacks/autopost_stack.py` | Set `POST_SCHEDULE` with 3 entries: `post_type` values like `"morning_motivation"`, `"midday_wisdom"`, `"evening_reflection"` |
| `lambda/content_generator/prompts.py` | Write prompts like: *"Generate an inspirational quote about perseverance. Include the quote, author attribution, and a 2-sentence caption for Facebook."* |
| `lambda/image_generator/image_prompts.py` | Prompt style: *"Serene sunrise landscape, soft warm colors, minimalist, no text"* |
| `lambda/post_scheduler/config.py` | Mirror the `POST_SCHEDULE` with `image_source` set to `"openai"` for AI backgrounds |

### Image source

Use **OpenAI DALL-E** for unique, mood-matched backgrounds. The Pillow overlay adds the quote text on top.

---

## Example 2: Local Business Promotions

**Use case:** A restaurant, gym, or shop that posts daily specials, tips, or promotions.

### Files to change

| File | What to change |
|---|---|
| `infra/stacks/autopost_stack.py` | Schedule posts for peak engagement: `"lunch_special"` at 10 AM, `"fitness_tip"` at 7 AM, `"weekend_promo"` on Fridays |
| `lambda/content_generator/prompts.py` | Prompts like: *"Write a Facebook post for a neighborhood pizza restaurant. Today's special is [dynamic]. Tone: friendly, casual, include a call-to-action."* |
| `lambda/image_generator/image_prompts.py` | Use food photography prompts: *"Appetizing overhead photo of artisan pizza, rustic wooden table, warm lighting"* |
| `lambda/post_scheduler/config.py` | Set `image_source` to `"unsplash"` for stock food photos, or `"openai"` for AI-generated images |

### Image source

Use **Unsplash** for realistic food/fitness/retail photography (free). Use **OpenAI** if you want stylized or branded visuals.

### Tips

- Rotate daily specials by including the day of the week in your prompt context.
- Use the `image_subtitle` field for pricing or promo codes on the overlay.

---

## Example 3: News / Data-Driven Content

**Use case:** A page that posts weather updates, stock market summaries, or sports scores.

### Files to change

| File | What to change |
|---|---|
| `infra/stacks/autopost_stack.py` | Schedule around data availability: `"morning_weather"` at 6 AM, `"market_close"` at 4:30 PM, `"sports_recap"` at 10 PM |
| `lambda/content_generator/prompts.py` | Prompts that reference external data: *"Summarize today's weather forecast for [city]. Include high/low temps, precipitation, and a practical tip."* |
| `lambda/content_generator/handler.py` | **Add an API call** before the LLM prompt to fetch live data (weather API, stock API, sports API). Pass the data into the prompt as context. |
| `lambda/image_generator/image_prompts.py` | Use infographic-style prompts or Unsplash weather/nature photos |

### Image source

Use **Unsplash** with dynamic keywords (e.g., search `"sunny cityscape"` or `"rainy street"` based on the weather data). Alternatively, use **OpenAI** to generate data visualization-style images.

### Tips

- Add external API secrets to Secrets Manager and grant read access to the Content Generator Lambda in the CDK stack.
- Use the `image_text` field to display key numbers (temperature, stock price, score) on the overlay.
- Consider error handling for when the external data API is unavailable.

---

## Overlay Styles

The Image Generator supports two Pillow overlay styles, configured via `OVERLAY_STYLE` in the CDK stack:

| Style | Dimensions | Best for |
|---|---|---|
| `"panel"` | 1080x1080 (square) | Quotes, tips, announcements |
| `"gradient"` | 1080x1350 (portrait) | Detailed content, multi-line text |

Both styles render the `image_text` as a headline, `image_subtitle` as secondary text, and `WATERMARK_TEXT` as a small brand watermark.

## Adding a New Post Type

1. Add an entry to `POST_SCHEDULE` in both `infra/stacks/autopost_stack.py` and `lambda/post_scheduler/config.py`.
2. Add a prompt mapping in `lambda/content_generator/prompts.py`.
3. Add an image prompt mapping in `lambda/image_generator/image_prompts.py`.
4. Run `cdk deploy` to create the new EventBridge rule.

No other code changes are needed -- the pipeline is driven entirely by configuration.
