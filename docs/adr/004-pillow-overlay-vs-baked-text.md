# ADR-004: Pillow Text Overlay Over AI-Generated Text in Images

## Status

Accepted

## Context

Each post includes an image with text overlay (quotes, tips, announcements). We needed to decide whether to ask the AI image generator to render text directly into the image or to generate a clean background image and overlay text programmatically with Pillow.

AI image generation models (DALL-E, Stable Diffusion) are notoriously unreliable at rendering text. They frequently produce misspellings, inconsistent letter spacing, wrong fonts, and unpredictable text placement.

## Decision

Generate clean background images with AI (no text), then overlay text programmatically using the Pillow (PIL) library in the image-generator Lambda.

Pillow handles font rendering, positioning, text wrapping, shadow/outline effects, and color selection. Font files are bundled in the Lambda deployment package.

## Consequences

**Pros:**
- Pixel-perfect control over typography, font choice, size, and color.
- Consistent text positioning and alignment across all posts.
- Brand consistency with approved fonts and style guidelines.
- No risk of AI-generated misspellings or garbled text.
- Text content can be changed without regenerating the background image.

**Cons:**
- Requires bundling font files in the Lambda package, increasing deployment size.
- Text layout logic (wrapping, sizing) must be implemented manually.
- Less "artistic" integration of text compared to what a perfect AI render could achieve.
