"""Tests for the Pillow text overlay module."""

import io

from PIL import Image

from image_generator.overlay import apply_text_overlay


def _make_test_image(width: int = 1536, height: int = 1024) -> bytes:
    """Create a simple test image and return its bytes."""
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


class TestPanelOverlay:
    """Test panel style overlay (1080x1080)."""

    def test_produces_valid_jpeg(self):
        result = apply_text_overlay(
            _make_test_image(),
            main_text="Test\nHeadline",
            subtitle_text="Test Brand",
            watermark="@TestPage",
            style="panel",
        )
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"
        assert img.size == (1080, 1080)

    def test_handles_empty_text(self):
        result = apply_text_overlay(
            _make_test_image(),
            main_text="",
            style="panel",
        )
        img = Image.open(io.BytesIO(result))
        assert img.size == (1080, 1080)

    def test_handles_long_text(self):
        long_text = "This is a very long headline\nthat spans multiple lines\nand tests wrapping"
        result = apply_text_overlay(
            _make_test_image(),
            main_text=long_text,
            style="panel",
        )
        img = Image.open(io.BytesIO(result))
        assert img.size == (1080, 1080)


class TestGradientOverlay:
    """Test gradient style overlay (1080x1350)."""

    def test_produces_valid_jpeg(self):
        result = apply_text_overlay(
            _make_test_image(1024, 1536),
            main_text="Test\nHeadline",
            subtitle_text="Test Brand",
            watermark="@TestPage",
            style="gradient",
        )
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"
        assert img.size == (1080, 1350)

    def test_handles_various_aspect_ratios(self):
        """Test that overlay handles different source image ratios."""
        for w, h in [(800, 600), (1920, 1080), (1024, 1536), (500, 500)]:
            result = apply_text_overlay(
                _make_test_image(w, h),
                main_text="Test",
                style="gradient",
            )
            img = Image.open(io.BytesIO(result))
            assert img.size == (1080, 1350)

    def test_default_style_is_panel(self):
        result = apply_text_overlay(
            _make_test_image(),
            main_text="Test",
        )
        img = Image.open(io.BytesIO(result))
        assert img.size == (1080, 1080)
