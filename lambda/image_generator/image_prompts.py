"""Base image prompts for AI image generation (fallback).

These are used when the content generator doesn't produce a content-driven
image prompt. Each post type has 3 variants for variety.

=============================================================================
CUSTOMIZE: Replace these with prompts that match YOUR content and brand.
=============================================================================
"""

import random

BASE_PROMPTS = {
    "YOUR_POST_TYPE_1": [
        (
            "Warm watercolor illustration with visible brushstrokes. "
            "A peaceful morning scene with golden sunlight streaming through trees. "
            "A person stands on a path looking toward the horizon with a sense of hope. "
            "Soft diffused side-light, warm palette of golds, corals, and soft greens. "
            "No text, no words, no letters, no watermarks, no logos."
        ),
        (
            "Digital illustration, cel-shaded style with clean lines. "
            "A cozy kitchen scene with morning light through a window, steam rising from a cup. "
            "Warm yellows and soft oranges dominate the palette. "
            "Bright directional morning sun creating long shadows. "
            "No text, no words, no letters, no watermarks, no logos."
        ),
        (
            "Impressionist oil painting with bold brushwork. "
            "A garden at sunrise with dew on flowers, a bench in the foreground. "
            "Rich golds, soft purples, and fresh greens in the palette. "
            "Backlighting creating a luminous glow around the scene. "
            "No text, no words, no letters, no watermarks, no logos."
        ),
    ],
    "YOUR_POST_TYPE_2": [
        (
            "Flat design illustration with clean geometric shapes. "
            "An overhead view of a busy desk with creative tools, notes, and a laptop. "
            "Terracotta, olive, cream, and teal color palette. "
            "Even, bright ambient lighting. Curious and friendly mood. "
            "No text, no words, no letters, no watermarks, no logos."
        ),
        (
            "Minimal vector illustration with bold outlines. "
            "A cityscape at midday with people walking, buildings in the background. "
            "Bright blues, warm oranges, and clean whites. "
            "Overhead sun with sharp shadows. Energetic and dynamic. "
            "No text, no words, no letters, no watermarks, no logos."
        ),
        (
            "Isometric illustration with vibrant colors. "
            "A small town scene with shops, trees, and people interacting. "
            "Pastel palette with coral, mint, and lavender accents. "
            "Soft ambient lighting with no harsh shadows. "
            "No text, no words, no letters, no watermarks, no logos."
        ),
    ],
    "YOUR_POST_TYPE_3": [
        (
            "Cinematic digital painting with dramatic lighting. "
            "A sunset over water with rich reflections, a figure silhouetted on a dock. "
            "Deep purples, warm magentas, and burnt oranges. "
            "Backlighting with rim light effect, golden hour warmth. "
            "No text, no words, no letters, no watermarks, no logos."
        ),
        (
            "Gouache painting with soft, matte textures. "
            "An evening scene with string lights over an outdoor gathering space. "
            "Warm amber, deep navy, and soft cream tones. "
            "Warm artificial light mixed with twilight blue sky. "
            "No text, no words, no letters, no watermarks, no logos."
        ),
        (
            "Watercolor wash with loose, flowing brushstrokes. "
            "A moonlit beach scene with gentle waves and stars overhead. "
            "Silver, deep blue, and pale gold palette. "
            "Cool moonlight with warm reflections on water. "
            "No text, no words, no letters, no watermarks, no logos."
        ),
    ],
}


def get_image_prompt(post_type: str) -> str:
    """Get a random base image prompt for the given post type."""
    prompts = BASE_PROMPTS.get(post_type)
    if not prompts:
        return (
            "A beautiful, inspiring scene with warm lighting and vibrant colors. "
            "One clear subject in focus with an emotional, compelling composition. "
            "No text, no words, no letters, no watermarks, no logos."
        )
    return random.choice(prompts)
