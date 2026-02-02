"""Tests for HTML sanitization."""

from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tweedle.utils.html_sanitizer import (
    sanitize_html,
    text_to_html,
    wrap_html_document,
)


class TestSanitizeHtml:
    """Tests for HTML sanitization."""

    def test_preserve_safe_tags(self):
        """Test that safe HTML tags are preserved."""
        html = "<p>Hello <b>World</b>!</p>"
        result = sanitize_html(html)

        assert "<p>" in result
        assert "<b>" in result
        assert "</b>" in result
        assert "</p>" in result

    def test_remove_script_tags(self):
        """Test that script tags are removed."""
        html = "<p>Hello</p><script>alert('xss')</script>"
        result = sanitize_html(html)

        assert "<script>" not in result
        assert "alert" not in result
        assert "<p>" in result

    def test_remove_event_handlers(self):
        """Test that event handlers are removed."""
        html = '<p onclick="alert(1)">Click me</p>'
        result = sanitize_html(html)

        assert "onclick" not in result
        assert "<p>" in result
        assert "Click me" in result

    def test_sanitize_javascript_href(self):
        """Test that javascript: URLs are removed."""
        html = '<a href="javascript:alert(1)">Click</a>'
        result = sanitize_html(html)

        assert "javascript:" not in result

    def test_preserve_safe_href(self):
        """Test that safe href URLs are preserved."""
        html = '<a href="https://example.com">Link</a>'
        result = sanitize_html(html)

        assert 'href="https://example.com"' in result

    def test_sanitize_style_expression(self):
        """Test that CSS expressions are removed."""
        html = '<div style="background: expression(alert(1))">Test</div>'
        result = sanitize_html(html)

        assert "expression" not in result

    def test_preserve_safe_style(self):
        """Test that safe CSS is preserved."""
        html = '<div style="color: red; font-size: 14px;">Text</div>'
        result = sanitize_html(html)

        assert "color: red" in result
        assert "font-size: 14px" in result

    def test_remove_unknown_tags(self):
        """Test that unknown tags are removed."""
        html = "<custom>Content</custom><p>Safe</p>"
        result = sanitize_html(html)

        assert "<custom>" not in result
        assert "Content" in result
        assert "<p>" in result

    def test_preserve_images(self):
        """Test that img tags are preserved with safe attributes."""
        html = '<img src="image.png" alt="Test" width="100">'
        result = sanitize_html(html)

        assert "<img" in result
        assert 'src="image.png"' in result
        assert 'alt="Test"' in result

    def test_sanitize_img_src_javascript(self):
        """Test that javascript: in img src is removed."""
        html = '<img src="javascript:alert(1)">'
        result = sanitize_html(html)

        assert "javascript:" not in result

    def test_preserve_tables(self):
        """Test that table elements are preserved."""
        html = "<table><tr><td>Cell</td></tr></table>"
        result = sanitize_html(html)

        assert "<table>" in result
        assert "<tr>" in result
        assert "<td>" in result

    def test_preserve_lists(self):
        """Test that list elements are preserved."""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = sanitize_html(html)

        assert "<ul>" in result
        assert "<li>" in result

    def test_empty_input(self):
        """Test handling empty input."""
        assert sanitize_html("") == ""
        assert sanitize_html(None) == ""

    def test_preserve_entities(self):
        """Test that HTML entities are preserved."""
        html = "<p>&amp; &lt; &gt; &quot;</p>"
        result = sanitize_html(html)

        assert "&amp;" in result
        assert "&lt;" in result
        assert "&gt;" in result


class TestTextToHtml:
    """Tests for text to HTML conversion."""

    def test_convert_plain_text(self):
        """Test converting plain text to HTML."""
        text = "Hello World"
        result = text_to_html(text)

        assert "Hello World" in result
        assert "<div" in result

    def test_convert_newlines(self):
        """Test that newlines are converted to <br>."""
        text = "Line 1\nLine 2"
        result = text_to_html(text)

        assert "<br>" in result

    def test_escape_html_chars(self):
        """Test that HTML characters are escaped."""
        text = "a < b && c > d"
        result = text_to_html(text)

        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result

    def test_linkify_urls(self):
        """Test that URLs are converted to links."""
        text = "Visit https://example.com for more"
        result = text_to_html(text)

        assert '<a href="https://example.com">' in result

    def test_empty_input(self):
        """Test handling empty input."""
        assert text_to_html("") == ""


class TestWrapHtmlDocument:
    """Tests for HTML document wrapping."""

    def test_wrap_body(self):
        """Test wrapping body content in document."""
        body = "<p>Content</p>"
        result = wrap_html_document(body)

        assert "<!DOCTYPE html>" in result
        assert "<html>" in result
        assert "<head>" in result
        assert "<body>" in result
        assert "<p>Content</p>" in result

    def test_wrap_with_title(self):
        """Test wrapping with custom title."""
        body = "<p>Content</p>"
        result = wrap_html_document(body, title="Test Title")

        assert "<title>Test Title</title>" in result

    def test_includes_stylesheet(self):
        """Test that default styles are included."""
        body = "<p>Content</p>"
        result = wrap_html_document(body)

        assert "<style>" in result
        assert "font-family" in result
