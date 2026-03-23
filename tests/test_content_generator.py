"""Tests for the Content Generator Lambda."""

from content_generator.handler import strip_markdown
from content_generator.prompts import get_content_prompt, get_image_text


class TestStripMarkdown:
    """Test markdown stripping for Facebook plain text."""

    def test_removes_bold(self):
        assert strip_markdown("This is **bold** text") == "This is bold text"

    def test_removes_italic(self):
        assert strip_markdown("This is *italic* text") == "This is italic text"

    def test_removes_headers(self):
        result = strip_markdown("## Header\nContent here")
        assert "##" not in result
        assert "Content here" in result

    def test_removes_links_keeps_text(self):
        result = strip_markdown("Click [here](https://example.com)")
        assert result == "Click here"

    def test_collapses_extra_newlines(self):
        result = strip_markdown("Line 1\n\n\n\n\nLine 2")
        assert result == "Line 1\n\nLine 2"

    def test_strips_whitespace(self):
        assert strip_markdown("  hello  ") == "hello"

    def test_handles_empty_string(self):
        assert strip_markdown("") == ""


class TestPrompts:
    """Test prompt template system."""

    def test_get_content_prompt_returns_system_and_user(self):
        prompt = get_content_prompt("YOUR_POST_TYPE_1", "2025-01-01")
        assert "system" in prompt
        assert "user" in prompt
        assert len(prompt["system"]) > 0
        assert len(prompt["user"]) > 0

    def test_get_content_prompt_formats_date(self):
        prompt = get_content_prompt("YOUR_POST_TYPE_1", "2025-06-15")
        assert "2025-06-15" in prompt["user"]

    def test_get_content_prompt_unknown_type_raises(self):
        import pytest

        with pytest.raises(ValueError, match="No prompt defined"):
            get_content_prompt("nonexistent-type", "2025-01-01")

    def test_get_image_text_returns_main_and_subtitle(self):
        result = get_image_text("YOUR_POST_TYPE_1")
        assert "main_text" in result
        assert "subtitle" in result

    def test_get_image_text_unknown_type_returns_default(self):
        result = get_image_text("nonexistent-type")
        assert "main_text" in result
        assert "subtitle" in result
