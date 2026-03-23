"""Text overlay compositing for generated images using Pillow.

Two overlay styles are available:

    "panel"    -- 1080x1080 square with a dark text panel at the bottom (1/3).
                  Clean, editorial look. Image fills top 2/3.

    "gradient" -- 1080x1350 portrait (4:5) with a gradient fade-to-black at
                  the bottom. Image fills the full canvas. Takes 45% more
                  mobile feed space than 1:1 square.

Set OVERLAY_STYLE env var to choose. Default: "panel".
"""

import io
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont


# --- Panel Style Constants (1:1 square) ---
PANEL_WIDTH = 1080
PANEL_HEIGHT = 1080
PANEL_IMAGE_HEIGHT = 720
PANEL_TEXT_HEIGHT = 360
PANEL_COLOR = (25, 25, 30)

# --- Gradient Style Constants (4:5 portrait) ---
GRADIENT_WIDTH = 1080
GRADIENT_HEIGHT = 1350
GRADIENT_FADE_HEIGHT = 500

# --- Shared Colors ---
ACCENT_GOLD = (255, 200, 50)
TEXT_WHITE = (255, 255, 255)
SHADOW_BLACK = (0, 0, 0)


def _load_font(fonts_dir: str, name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font from the fonts directory, fall back to default."""
    font_path = os.path.join(fonts_dir, name)
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def _smart_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Center-crop an image to match the target aspect ratio."""
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if abs(src_ratio - target_ratio) < 0.01:
        return img

    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        return img.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        return img.crop((0, top, src_w, top + new_h))


def _draw_gradient(canvas: Image.Image, start_y: int, height: int) -> None:
    """Draw a bottom-to-top gradient from black to transparent on the canvas."""
    gradient = Image.new("RGBA", (canvas.width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    for y in range(height):
        alpha = int(210 * (y / height) ** 1.5)
        draw.line([(0, y), (canvas.width, y)], fill=(0, 0, 0, alpha))

    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(gradient, (0, start_y), gradient)
    canvas.paste(canvas_rgba.convert("RGB"))


def _wrap_lines(text: str, max_chars: int) -> list[str]:
    """Split text into lines and auto-wrap any that exceed max_chars."""
    lines = text.split("\n")
    wrapped = []
    for line in lines:
        if len(line) > max_chars:
            wrapped.extend(textwrap.wrap(line, width=max_chars))
        else:
            wrapped.append(line)
    return wrapped


def _draw_text_block(
    draw: ImageDraw.Draw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    canvas_width: int,
    text_area_top: int,
    text_area_bottom: int,
    line_height: int,
) -> None:
    """Draw centered text lines with shadow in the given area."""
    total_height = len(lines) * line_height
    center_y = (text_area_top + text_area_bottom) // 2
    start_y = center_y - total_height // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (canvas_width - text_width) // 2
        y = start_y + i * line_height

        draw.text((x + 2, y + 2), line, fill=SHADOW_BLACK, font=font)
        draw.text((x, y), line, fill=TEXT_WHITE, font=font)


def _apply_panel_overlay(
    image_bytes: bytes, main_text: str, subtitle_text: str, watermark: str, fonts_dir: str
) -> bytes:
    """Panel style: 1080x1080 square with dark text panel at bottom."""
    src = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    src = _smart_crop(src, PANEL_WIDTH, PANEL_IMAGE_HEIGHT)
    src = src.resize((PANEL_WIDTH, PANEL_IMAGE_HEIGHT), Image.LANCZOS)

    canvas = Image.new("RGB", (PANEL_WIDTH, PANEL_HEIGHT), PANEL_COLOR)
    canvas.paste(src, (0, 0))
    draw = ImageDraw.Draw(canvas)

    font_bold = _load_font(fonts_dir, "EBGaramond-Bold.ttf", 48)
    font_regular = _load_font(fonts_dir, "EBGaramond-Regular.ttf", 28)
    font_watermark = _load_font(fonts_dir, "EBGaramond-Regular.ttf", 22)

    if main_text:
        lines = _wrap_lines(main_text, 24)
        if len(lines) > 3:
            font_bold = _load_font(fonts_dir, "EBGaramond-Bold.ttf", 40)
            lh = 50
        else:
            lh = 58
        _draw_text_block(draw, lines, font_bold, PANEL_WIDTH, PANEL_IMAGE_HEIGHT + 25, PANEL_HEIGHT - 60, lh)

    if subtitle_text:
        subtitle_y = PANEL_HEIGHT - 50
        bbox = draw.textbbox((0, 0), subtitle_text, font=font_regular)
        tw = bbox[2] - bbox[0]
        x = (PANEL_WIDTH - tw) // 2
        draw.text((x + 1, subtitle_y + 1), subtitle_text, fill=SHADOW_BLACK, font=font_regular)
        draw.text((x, subtitle_y), subtitle_text, fill=(255, 215, 0), font=font_regular)

    if watermark:
        bbox = draw.textbbox((0, 0), watermark, font=font_watermark)
        tw = bbox[2] - bbox[0]
        x = PANEL_WIDTH - tw - 20
        draw.text((x + 1, 16), watermark, fill=(50, 50, 50), font=font_watermark)
        draw.text((x, 15), watermark, fill=(220, 220, 220), font=font_watermark)

    output = io.BytesIO()
    canvas.save(output, format="JPEG", quality=90)
    output.seek(0)
    return output.read()


def _apply_gradient_overlay(
    image_bytes: bytes, main_text: str, subtitle_text: str, watermark: str, fonts_dir: str
) -> bytes:
    """Gradient style: 1080x1350 portrait (4:5) with fade-to-black overlay."""
    src = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Resize to cover full canvas
    src_ratio = src.width / src.height
    canvas_ratio = GRADIENT_WIDTH / GRADIENT_HEIGHT

    if src_ratio > canvas_ratio:
        new_height = GRADIENT_HEIGHT
        new_width = int(GRADIENT_HEIGHT * src_ratio)
    else:
        new_width = GRADIENT_WIDTH
        new_height = int(GRADIENT_WIDTH / src_ratio)

    src = src.resize((new_width, new_height), Image.LANCZOS)
    left = (new_width - GRADIENT_WIDTH) // 2
    top = (new_height - GRADIENT_HEIGHT) // 2
    src = src.crop((left, top, left + GRADIENT_WIDTH, top + GRADIENT_HEIGHT))

    canvas = src.copy()
    _draw_gradient(canvas, GRADIENT_HEIGHT - GRADIENT_FADE_HEIGHT, GRADIENT_FADE_HEIGHT)

    draw = ImageDraw.Draw(canvas)

    font_bold = _load_font(fonts_dir, "Poppins-Bold.ttf", 52)
    font_regular = _load_font(fonts_dir, "Poppins-Regular.ttf", 30)
    font_watermark = _load_font(fonts_dir, "Poppins-Regular.ttf", 20)

    if main_text:
        text_area_top = GRADIENT_HEIGHT - GRADIENT_FADE_HEIGHT + 140
        text_area_bottom = GRADIENT_HEIGHT - 80
        lines = _wrap_lines(main_text, 22)
        if len(lines) > 3:
            font_bold = _load_font(fonts_dir, "Poppins-Bold.ttf", 42)
            lh = 52
        else:
            lh = 64

        total_height = len(lines) * lh
        center_y = (text_area_top + text_area_bottom) // 2
        start_y = center_y - total_height // 2

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font_bold)
            tw = bbox[2] - bbox[0]
            x = (GRADIENT_WIDTH - tw) // 2
            y = start_y + i * lh
            draw.text((x + 2, y + 2), line, fill=SHADOW_BLACK, font=font_bold)
            draw.text((x + 1, y + 1), line, fill=SHADOW_BLACK, font=font_bold)
            draw.text((x, y), line, fill=TEXT_WHITE, font=font_bold)

    if subtitle_text:
        subtitle_y = GRADIENT_HEIGHT - 65
        bbox = draw.textbbox((0, 0), subtitle_text, font=font_regular)
        tw = bbox[2] - bbox[0]
        x = (GRADIENT_WIDTH - tw) // 2
        draw.text((x + 1, subtitle_y + 1), subtitle_text, fill=SHADOW_BLACK, font=font_regular)
        draw.text((x, subtitle_y), subtitle_text, fill=ACCENT_GOLD, font=font_regular)

    if watermark:
        bbox = draw.textbbox((0, 0), watermark, font=font_watermark)
        tw = bbox[2] - bbox[0]
        x = GRADIENT_WIDTH - tw - 20
        draw.text((x + 1, 16), watermark, fill=(30, 30, 30), font=font_watermark)
        draw.text((x, 15), watermark, fill=(200, 200, 200), font=font_watermark)

    output = io.BytesIO()
    canvas.save(output, format="JPEG", quality=92)
    output.seek(0)
    return output.read()


def apply_text_overlay(
    image_bytes: bytes,
    main_text: str,
    subtitle_text: str = "",
    watermark: str = "",
    fonts_dir: str = "/var/task/fonts",
    style: str = "panel",
) -> bytes:
    """Apply text overlay to an image and return the composited JPEG bytes.

    Args:
        image_bytes: Raw image bytes (PNG or JPEG from OpenAI or Unsplash)
        main_text:   Bold headline text (supports \\n for line breaks)
        subtitle_text: Smaller text below headline (brand name, category, etc.)
        watermark:   Small text in top-right corner (page name)
        fonts_dir:   Path to directory containing TTF font files
        style:       "panel" (1080x1080) or "gradient" (1080x1350)
    """
    if style == "gradient":
        return _apply_gradient_overlay(image_bytes, main_text, subtitle_text, watermark, fonts_dir)
    return _apply_panel_overlay(image_bytes, main_text, subtitle_text, watermark, fonts_dir)
