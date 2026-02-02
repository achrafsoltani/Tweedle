"""Email message model and parsing."""

import email
import email.utils
import email.header
from email.message import EmailMessage
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import base64
import quopri


@dataclass
class Attachment:
    """Email attachment."""
    filename: str
    content_type: str
    data: bytes
    size: int


@dataclass
class EmailAddress:
    """Parsed email address."""
    name: str
    address: str

    def __str__(self) -> str:
        if self.name:
            return f"{self.name} <{self.address}>"
        return self.address

    @classmethod
    def parse(cls, raw: str) -> "EmailAddress":
        """Parse an email address string."""
        name, addr = email.utils.parseaddr(raw)
        return cls(name=name, address=addr)

    @classmethod
    def parse_list(cls, raw: str) -> list["EmailAddress"]:
        """Parse a comma-separated list of email addresses."""
        if not raw:
            return []
        addresses = email.utils.getaddresses([raw])
        return [cls(name=name, address=addr) for name, addr in addresses]


@dataclass
class Message:
    """Email message model."""
    uid: int
    message_id: str = ""
    subject: str = ""
    from_addr: Optional[EmailAddress] = None
    to_addrs: list[EmailAddress] = field(default_factory=list)
    cc_addrs: list[EmailAddress] = field(default_factory=list)
    bcc_addrs: list[EmailAddress] = field(default_factory=list)
    reply_to: Optional[EmailAddress] = None
    date: Optional[datetime] = None
    text_body: str = ""
    html_body: str = ""
    attachments: list[Attachment] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)
    folder: str = ""

    @property
    def is_read(self) -> bool:
        return "\\Seen" in self.flags

    @property
    def is_flagged(self) -> bool:
        return "\\Flagged" in self.flags

    @property
    def is_answered(self) -> bool:
        return "\\Answered" in self.flags

    @property
    def has_attachments(self) -> bool:
        return len(self.attachments) > 0

    @property
    def display_from(self) -> str:
        """Get display-friendly from address."""
        if self.from_addr:
            return self.from_addr.name or self.from_addr.address
        return ""

    @property
    def display_date(self) -> str:
        """Get display-friendly date."""
        if self.date:
            now = datetime.now()
            if self.date.date() == now.date():
                return self.date.strftime("%H:%M")
            elif self.date.year == now.year:
                return self.date.strftime("%b %d")
            else:
                return self.date.strftime("%Y-%m-%d")
        return ""

    @property
    def body(self) -> str:
        """Get the preferred body (HTML if available, otherwise text)."""
        return self.html_body or self.text_body


def decode_header_value(value: str) -> str:
    """Decode an email header value."""
    if not value:
        return ""
    decoded_parts = []
    for part, charset in email.header.decode_header(value):
        if isinstance(part, bytes):
            charset = charset or "utf-8"
            try:
                decoded_parts.append(part.decode(charset, errors="replace"))
            except (LookupError, UnicodeDecodeError):
                decoded_parts.append(part.decode("utf-8", errors="replace"))
        else:
            decoded_parts.append(part)
    return "".join(decoded_parts)


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse an email date string."""
    if not date_str:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def decode_payload(part: EmailMessage) -> str:
    """Decode the payload of a message part."""
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""

    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except (LookupError, UnicodeDecodeError):
        return payload.decode("utf-8", errors="replace")


def parse_message(uid: int, raw_data: bytes, flags: set[str] = None, folder: str = "") -> Message:
    """Parse raw email data into a Message object."""
    msg = email.message_from_bytes(raw_data)

    message = Message(
        uid=uid,
        message_id=msg.get("Message-ID", ""),
        subject=decode_header_value(msg.get("Subject", "")),
        from_addr=EmailAddress.parse(msg.get("From", "")),
        to_addrs=EmailAddress.parse_list(msg.get("To", "")),
        cc_addrs=EmailAddress.parse_list(msg.get("Cc", "")),
        bcc_addrs=EmailAddress.parse_list(msg.get("Bcc", "")),
        date=parse_date(msg.get("Date", "")),
        flags=flags or set(),
        folder=folder,
    )

    reply_to = msg.get("Reply-To")
    if reply_to:
        message.reply_to = EmailAddress.parse(reply_to)

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = part.get("Content-Disposition", "")

            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    filename = decode_header_value(filename)
                    data = part.get_payload(decode=True) or b""
                    message.attachments.append(Attachment(
                        filename=filename,
                        content_type=content_type,
                        data=data,
                        size=len(data),
                    ))
            elif content_type == "text/plain" and not message.text_body:
                message.text_body = decode_payload(part)
            elif content_type == "text/html" and not message.html_body:
                message.html_body = decode_payload(part)
    else:
        content_type = msg.get_content_type()
        if content_type == "text/plain":
            message.text_body = decode_payload(msg)
        elif content_type == "text/html":
            message.html_body = decode_payload(msg)

    return message


@dataclass
class MessageHeader:
    """Lightweight message header for list display."""
    uid: int
    subject: str
    from_addr: str
    date: Optional[datetime]
    flags: set[str]
    size: int = 0

    @property
    def is_read(self) -> bool:
        return "\\Seen" in self.flags

    @property
    def is_flagged(self) -> bool:
        return "\\Flagged" in self.flags

    @property
    def display_date(self) -> str:
        if self.date:
            now = datetime.now()
            if self.date.date() == now.date():
                return self.date.strftime("%H:%M")
            elif self.date.year == now.year:
                return self.date.strftime("%b %d")
            else:
                return self.date.strftime("%Y-%m-%d")
        return ""


def parse_message_header(uid: int, envelope: dict, flags: set[str]) -> MessageHeader:
    """Parse IMAP envelope data into a MessageHeader."""
    subject = ""
    if envelope.subject:
        subject = decode_header_value(
            envelope.subject.decode("utf-8", errors="replace")
            if isinstance(envelope.subject, bytes)
            else envelope.subject
        )

    from_addr = ""
    if envelope.from_ and len(envelope.from_) > 0:
        addr = envelope.from_[0]
        name = ""
        if addr.name:
            name = addr.name.decode("utf-8", errors="replace") if isinstance(addr.name, bytes) else addr.name
            name = decode_header_value(name)
        mailbox = addr.mailbox.decode("utf-8", errors="replace") if isinstance(addr.mailbox, bytes) else (addr.mailbox or "")
        host = addr.host.decode("utf-8", errors="replace") if isinstance(addr.host, bytes) else (addr.host or "")
        email_addr = f"{mailbox}@{host}" if mailbox and host else ""
        from_addr = name or email_addr

    date = None
    if envelope.date:
        date = parse_date(
            envelope.date.decode("utf-8", errors="replace")
            if isinstance(envelope.date, bytes)
            else str(envelope.date)
        )

    return MessageHeader(
        uid=uid,
        subject=subject,
        from_addr=from_addr,
        date=date,
        flags=flags,
    )
