"""Tests for message parsing."""

from datetime import datetime
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tweedle.core.message import (
    EmailAddress,
    Attachment,
    Message,
    MessageHeader,
    parse_message,
    decode_header_value,
    parse_date,
)


class TestEmailAddress:
    """Tests for EmailAddress class."""

    def test_parse_simple_address(self):
        """Test parsing a simple email address."""
        addr = EmailAddress.parse("test@example.com")

        assert addr.address == "test@example.com"
        assert addr.name == ""

    def test_parse_address_with_name(self):
        """Test parsing address with display name."""
        addr = EmailAddress.parse("John Doe <john@example.com>")

        assert addr.address == "john@example.com"
        assert addr.name == "John Doe"

    def test_parse_address_with_quoted_name(self):
        """Test parsing address with quoted name."""
        addr = EmailAddress.parse('"Doe, John" <john@example.com>')

        assert addr.address == "john@example.com"
        assert addr.name == "Doe, John"

    def test_str_with_name(self):
        """Test string representation with name."""
        addr = EmailAddress(name="John Doe", address="john@example.com")

        assert str(addr) == "John Doe <john@example.com>"

    def test_str_without_name(self):
        """Test string representation without name."""
        addr = EmailAddress(name="", address="john@example.com")

        assert str(addr) == "john@example.com"

    def test_parse_list(self):
        """Test parsing a list of addresses."""
        addrs = EmailAddress.parse_list(
            "John <john@example.com>, Jane <jane@example.com>"
        )

        assert len(addrs) == 2
        assert addrs[0].address == "john@example.com"
        assert addrs[1].address == "jane@example.com"

    def test_parse_empty_list(self):
        """Test parsing empty address list."""
        addrs = EmailAddress.parse_list("")

        assert addrs == []


class TestDecodeHeaderValue:
    """Tests for header decoding."""

    def test_decode_plain_text(self):
        """Test decoding plain ASCII text."""
        result = decode_header_value("Hello World")

        assert result == "Hello World"

    def test_decode_utf8_encoded(self):
        """Test decoding UTF-8 encoded header."""
        # =?utf-8?b?...?= format
        result = decode_header_value("=?utf-8?b?SGVsbG8gV29ybGQ=?=")

        assert result == "Hello World"

    def test_decode_quoted_printable(self):
        """Test decoding quoted-printable header."""
        result = decode_header_value("=?utf-8?q?Hello_World?=")

        assert result == "Hello World"

    def test_decode_empty(self):
        """Test decoding empty string."""
        result = decode_header_value("")

        assert result == ""

    def test_decode_none(self):
        """Test decoding None."""
        result = decode_header_value(None)

        assert result == ""


class TestParseDate:
    """Tests for date parsing."""

    def test_parse_rfc2822_date(self):
        """Test parsing RFC 2822 date format."""
        result = parse_date("Mon, 15 Jan 2024 10:30:00 +0000")

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_empty_date(self):
        """Test parsing empty date string."""
        result = parse_date("")

        assert result is None

    def test_parse_invalid_date(self):
        """Test parsing invalid date string."""
        result = parse_date("not a date")

        assert result is None


class TestMessage:
    """Tests for Message class."""

    def test_create_message(self):
        """Test creating a Message."""
        msg = Message(
            uid=123,
            subject="Test Subject",
            from_addr=EmailAddress(name="John", address="john@example.com"),
            to_addrs=[EmailAddress(name="Jane", address="jane@example.com")],
            date=datetime(2024, 1, 15, 10, 30),
            text_body="Hello, World!",
            flags={"\\Seen"},
        )

        assert msg.uid == 123
        assert msg.subject == "Test Subject"
        assert msg.is_read is True
        assert msg.display_from == "John"

    def test_message_unread(self):
        """Test unread message."""
        msg = Message(uid=1, flags=set())

        assert msg.is_read is False

    def test_message_flagged(self):
        """Test flagged message."""
        msg = Message(uid=1, flags={"\\Flagged"})

        assert msg.is_flagged is True

    def test_message_has_attachments(self):
        """Test message with attachments."""
        msg = Message(
            uid=1,
            attachments=[
                Attachment(
                    filename="test.pdf",
                    content_type="application/pdf",
                    data=b"data",
                    size=4,
                )
            ],
        )

        assert msg.has_attachments is True

    def test_message_body_prefers_html(self):
        """Test that body property prefers HTML."""
        msg = Message(
            uid=1,
            text_body="Plain text",
            html_body="<html>HTML</html>",
        )

        assert msg.body == "<html>HTML</html>"

    def test_message_body_falls_back_to_text(self):
        """Test that body property falls back to text."""
        msg = Message(
            uid=1,
            text_body="Plain text",
            html_body="",
        )

        assert msg.body == "Plain text"


class TestParseMessage:
    """Tests for message parsing."""

    def test_parse_simple_text_message(self):
        """Test parsing a simple text message."""
        raw = b"""From: sender@example.com
To: recipient@example.com
Subject: Test Subject
Date: Mon, 15 Jan 2024 10:30:00 +0000
Message-ID: <test@example.com>

This is the message body.
"""
        msg = parse_message(123, raw, {"\\Seen"})

        assert msg.uid == 123
        assert msg.subject == "Test Subject"
        assert msg.from_addr.address == "sender@example.com"
        assert len(msg.to_addrs) == 1
        assert msg.to_addrs[0].address == "recipient@example.com"
        assert "This is the message body." in msg.text_body
        assert msg.is_read is True

    def test_parse_multipart_message(self):
        """Test parsing a multipart message."""
        raw = b"""From: sender@example.com
To: recipient@example.com
Subject: Multipart Test
Date: Mon, 15 Jan 2024 10:30:00 +0000
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset="utf-8"

Plain text version.
--boundary123
Content-Type: text/html; charset="utf-8"

<html><body>HTML version.</body></html>
--boundary123--
"""
        msg = parse_message(456, raw)

        assert msg.uid == 456
        assert "Plain text version" in msg.text_body
        assert "<html>" in msg.html_body


class TestMessageHeader:
    """Tests for MessageHeader class."""

    def test_create_header(self):
        """Test creating a MessageHeader."""
        header = MessageHeader(
            uid=123,
            subject="Test",
            from_addr="john@example.com",
            date=datetime(2024, 1, 15, 10, 30),
            flags={"\\Seen"},
        )

        assert header.uid == 123
        assert header.is_read is True

    def test_header_display_date_today(self):
        """Test display date for today's message."""
        now = datetime.now()
        header = MessageHeader(
            uid=1,
            subject="Test",
            from_addr="test@example.com",
            date=now.replace(hour=14, minute=30),
            flags=set(),
        )

        assert "14:30" in header.display_date

    def test_header_display_date_this_year(self):
        """Test display date for message this year."""
        header = MessageHeader(
            uid=1,
            subject="Test",
            from_addr="test@example.com",
            date=datetime(datetime.now().year, 6, 15),
            flags=set(),
        )

        assert "Jun" in header.display_date
        assert "15" in header.display_date
