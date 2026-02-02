"""SMTP client for sending emails."""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path
from typing import Optional

from tweedle.core.account import Account


class SMTPClientWrapper:
    """Wrapper around smtplib for sending emails."""

    def __init__(self, account: Account):
        self.account = account

    def send_message(
        self,
        to: list[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        reply_to: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None,
        attachments: Optional[list[tuple[str, bytes, str]]] = None,
    ) -> None:
        """
        Send an email message.

        Args:
            to: List of recipient addresses
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            reply_to: Optional Reply-To address
            in_reply_to: Message-ID of the message being replied to
            references: References header for threading
            attachments: List of (filename, data, content_type) tuples
        """
        config = self.account.config

        if html_body or attachments:
            msg = MIMEMultipart("mixed")
            body_part = MIMEMultipart("alternative")
            body_part.attach(MIMEText(body, "plain", "utf-8"))
            if html_body:
                body_part.attach(MIMEText(html_body, "html", "utf-8"))
            msg.attach(body_part)
        else:
            msg = MIMEText(body, "plain", "utf-8")

        from_name = self.account.name or ""
        from_addr = config.email
        msg["From"] = formataddr((from_name, from_addr))

        msg["To"] = ", ".join(to)

        if cc:
            msg["Cc"] = ", ".join(cc)

        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain=from_addr.split("@")[-1])

        if reply_to:
            msg["Reply-To"] = reply_to

        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to

        if references:
            msg["References"] = references

        if attachments:
            for filename, data, content_type in attachments:
                maintype, subtype = content_type.split("/", 1) if "/" in content_type else ("application", "octet-stream")
                part = MIMEBase(maintype, subtype)
                part.set_payload(data)
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=filename,
                )
                msg.attach(part)

        all_recipients = list(to)
        if cc:
            all_recipients.extend(cc)
        if bcc:
            all_recipients.extend(bcc)

        password = self.account.password
        if not password:
            raise ValueError("No password available")

        if config.smtp_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                config.smtp_server,
                config.smtp_port,
                context=context,
            ) as server:
                server.login(config.email, password)
                server.sendmail(from_addr, all_recipients, msg.as_string())
        else:
            with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
                if config.smtp_starttls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                server.login(config.email, password)
                server.sendmail(from_addr, all_recipients, msg.as_string())

    def send_reply(
        self,
        original_message_id: str,
        original_references: Optional[str],
        to: list[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[list[str]] = None,
        attachments: Optional[list[tuple[str, bytes, str]]] = None,
    ) -> None:
        """Send a reply to an existing message."""
        references = original_message_id
        if original_references:
            references = f"{original_references} {original_message_id}"

        self.send_message(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
            cc=cc,
            in_reply_to=original_message_id,
            references=references,
            attachments=attachments,
        )

    def send_forward(
        self,
        to: list[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[list[tuple[str, bytes, str]]] = None,
    ) -> None:
        """Forward a message."""
        self.send_message(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
            attachments=attachments,
        )


def load_attachment_from_file(filepath: str) -> tuple[str, bytes, str]:
    """Load an attachment from a file path."""
    import mimetypes

    path = Path(filepath)
    filename = path.name
    data = path.read_bytes()

    content_type, _ = mimetypes.guess_type(filepath)
    if not content_type:
        content_type = "application/octet-stream"

    return (filename, data, content_type)
