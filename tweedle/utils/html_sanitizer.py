"""HTML sanitizer for safe email display."""

import re
from html.parser import HTMLParser
from typing import Optional


ALLOWED_TAGS = {
    "html", "head", "body", "style",
    "div", "span", "p", "br", "hr",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "img",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption", "colgroup", "col",
    "ul", "ol", "li", "dl", "dt", "dd",
    "b", "i", "u", "s", "em", "strong", "code", "pre", "blockquote", "cite",
    "sub", "sup", "small", "big",
    "font", "center",
    "article", "section", "nav", "aside", "header", "footer", "main",
}

ALLOWED_ATTRS = {
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "title", "width", "height"},
    "table": {"border", "cellpadding", "cellspacing", "width", "align"},
    "td": {"colspan", "rowspan", "align", "valign", "width"},
    "th": {"colspan", "rowspan", "align", "valign", "width"},
    "tr": {"align", "valign"},
    "font": {"color", "size", "face"},
    "div": {"align"},
    "p": {"align"},
    "img": {"src", "alt", "width", "height"},
}

GLOBAL_ATTRS = {"class", "id", "style", "dir", "lang"}

DANGEROUS_PROTOCOLS = {"javascript", "vbscript", "data"}


class HTMLSanitizer(HTMLParser):
    """Parser that sanitizes HTML content."""

    def __init__(self):
        super().__init__()
        self.result = []
        self.in_script = False
        self.in_style = False
        self.style_content = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]):
        tag_lower = tag.lower()

        if tag_lower == "script":
            self.in_script = True
            return

        if tag_lower == "style":
            self.in_style = True
            self.style_content = []
            return

        if tag_lower not in ALLOWED_TAGS:
            return

        safe_attrs = []
        allowed = ALLOWED_ATTRS.get(tag_lower, set()) | GLOBAL_ATTRS

        for name, value in attrs:
            name_lower = name.lower()

            if name_lower not in allowed:
                continue

            if name_lower == "href" or name_lower == "src":
                if value:
                    protocol = value.split(":")[0].lower() if ":" in value else ""
                    if protocol in DANGEROUS_PROTOCOLS:
                        continue

            if name_lower == "style" and value:
                value = self._sanitize_style(value)

            if value is not None:
                safe_attrs.append(f'{name_lower}="{self._escape_attr(value)}"')
            else:
                safe_attrs.append(name_lower)

        if safe_attrs:
            self.result.append(f"<{tag_lower} {' '.join(safe_attrs)}>")
        else:
            self.result.append(f"<{tag_lower}>")

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()

        if tag_lower == "script":
            self.in_script = False
            return

        if tag_lower == "style":
            self.in_style = False
            style_css = "".join(self.style_content)
            sanitized_css = self._sanitize_css(style_css)
            if sanitized_css:
                self.result.append(f"<style>{sanitized_css}</style>")
            return

        if tag_lower in ALLOWED_TAGS:
            self.result.append(f"</{tag_lower}>")

    def handle_data(self, data: str):
        if self.in_script:
            return

        if self.in_style:
            self.style_content.append(data)
            return

        self.result.append(self._escape_data(data))

    def handle_entityref(self, name: str):
        if not self.in_script:
            self.result.append(f"&{name};")

    def handle_charref(self, name: str):
        if not self.in_script:
            self.result.append(f"&#{name};")

    def _escape_attr(self, value: str) -> str:
        """Escape attribute value."""
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def _escape_data(self, data: str) -> str:
        """Escape text content (minimal escaping since we're inside HTML)."""
        return data

    def _sanitize_style(self, style: str) -> str:
        """Sanitize inline style attribute."""
        dangerous_patterns = [
            r"expression\s*\(",
            r"javascript\s*:",
            r"vbscript\s*:",
            r"behavior\s*:",
            r"-moz-binding\s*:",
            r"@import",
        ]

        for pattern in dangerous_patterns:
            style = re.sub(pattern, "", style, flags=re.IGNORECASE)

        return style

    def _sanitize_css(self, css: str) -> str:
        """Sanitize CSS content."""
        dangerous_patterns = [
            r"expression\s*\([^)]*\)",
            r"javascript\s*:[^;]*",
            r"vbscript\s*:[^;]*",
            r"behavior\s*:[^;]*",
            r"-moz-binding\s*:[^;]*",
            r"@import[^;]*;",
        ]

        for pattern in dangerous_patterns:
            css = re.sub(pattern, "", css, flags=re.IGNORECASE)

        return css

    def get_result(self) -> str:
        """Get the sanitized HTML."""
        return "".join(self.result)


def sanitize_html(html: str) -> str:
    """Sanitize HTML content for safe display."""
    if not html:
        return ""

    sanitizer = HTMLSanitizer()
    try:
        sanitizer.feed(html)
        return sanitizer.get_result()
    except Exception:
        return html.replace("<", "&lt;").replace(">", "&gt;")


def text_to_html(text: str) -> str:
    """Convert plain text to simple HTML."""
    if not text:
        return ""

    html = text.replace("&", "&amp;")
    html = html.replace("<", "&lt;")
    html = html.replace(">", "&gt;")
    html = html.replace("\n", "<br>\n")

    url_pattern = r'(https?://[^\s<>"]+)'
    html = re.sub(url_pattern, r'<a href="\1">\1</a>', html)

    return f"<div style='font-family: monospace; white-space: pre-wrap;'>{html}</div>"


def wrap_html_document(body: str, title: str = "") -> str:
    """Wrap HTML content in a complete document."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 14px;
            line-height: 1.5;
            color: #333;
            margin: 10px;
            background: white;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        a {{
            color: #0066cc;
        }}
        pre, code {{
            background: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: monospace;
        }}
        pre {{
            padding: 10px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 3px solid #ddd;
            margin-left: 0;
            padding-left: 15px;
            color: #666;
        }}
        table {{
            border-collapse: collapse;
        }}
        td, th {{
            padding: 5px 10px;
        }}
    </style>
</head>
<body>
{body}
</body>
</html>"""
