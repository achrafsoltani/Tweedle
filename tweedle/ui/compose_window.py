"""Email composition window."""

from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QToolBar,
    QStatusBar,
    QLabel,
    QMessageBox,
    QSplitter,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction, QKeySequence, QFont

from tweedle.core.account import Account
from tweedle.core.message import Message
from tweedle.core.workers import SendMessageWorker
from tweedle.ui.attachment_widget import AttachmentSelector


class ComposeWindow(QMainWindow):
    """Window for composing email messages."""

    message_sent = Signal()

    def __init__(self, account: Account, parent=None):
        super().__init__(parent)
        self.account = account
        self._reply_message: Optional[Message] = None
        self._worker: Optional[SendMessageWorker] = None

        self.setWindowTitle("New Message")
        self.resize(700, 500)

        self._setup_ui()
        self._setup_toolbar()
        self._setup_statusbar()

    def _setup_ui(self):
        """Set up the UI."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header_layout = QFormLayout()
        header_layout.setSpacing(5)

        self.from_label = QLabel(f"{self.account.name} <{self.account.email}>")
        header_layout.addRow("From:", self.from_label)

        self.to_edit = QLineEdit()
        self.to_edit.setPlaceholderText("recipient@example.com")
        header_layout.addRow("To:", self.to_edit)

        self.cc_edit = QLineEdit()
        self.cc_edit.setPlaceholderText("cc@example.com (optional)")
        header_layout.addRow("Cc:", self.cc_edit)

        self.bcc_edit = QLineEdit()
        self.bcc_edit.setPlaceholderText("bcc@example.com (optional)")
        header_layout.addRow("Bcc:", self.bcc_edit)

        self.subject_edit = QLineEdit()
        self.subject_edit.setPlaceholderText("Subject")
        header_layout.addRow("Subject:", self.subject_edit)

        layout.addLayout(header_layout)

        self.attachment_selector = AttachmentSelector()
        layout.addWidget(self.attachment_selector)

        self.body_edit = QTextEdit()
        self.body_edit.setAcceptRichText(False)
        font = QFont("Monospace")
        font.setStyleHint(QFont.Monospace)
        self.body_edit.setFont(font)
        layout.addWidget(self.body_edit, 1)

    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar("Compose")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        send_action = QAction("Send", self)
        send_action.setShortcut(QKeySequence("Ctrl+Return"))
        send_action.triggered.connect(self._on_send)
        toolbar.addAction(send_action)

        toolbar.addSeparator()

        attach_action = QAction("Attach", self)
        attach_action.triggered.connect(self._on_attach)
        toolbar.addAction(attach_action)

        toolbar.addSeparator()

        discard_action = QAction("Discard", self)
        discard_action.triggered.connect(self.close)
        toolbar.addAction(discard_action)

    def _setup_statusbar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

    def setup_reply(self, message: Message, reply_all: bool = False):
        """Set up the window for replying to a message."""
        self._reply_message = message

        self.setWindowTitle(f"Re: {message.subject}")

        if message.reply_to:
            self.to_edit.setText(str(message.reply_to))
        elif message.from_addr:
            self.to_edit.setText(str(message.from_addr))

        if reply_all:
            cc_addrs = []

            for addr in message.to_addrs:
                if addr.address.lower() != self.account.email.lower():
                    cc_addrs.append(str(addr))

            for addr in message.cc_addrs:
                if addr.address.lower() != self.account.email.lower():
                    cc_addrs.append(str(addr))

            if cc_addrs:
                self.cc_edit.setText(", ".join(cc_addrs))

        subject = message.subject
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        self.subject_edit.setText(subject)

        original_date = ""
        if message.date:
            original_date = message.date.strftime("%B %d, %Y at %I:%M %p")

        original_from = str(message.from_addr) if message.from_addr else "Unknown"

        quoted_body = ""
        original_text = message.text_body or self._html_to_plain(message.html_body)
        for line in original_text.split("\n"):
            quoted_body += f"> {line}\n"

        body = f"\n\n\nOn {original_date}, {original_from} wrote:\n{quoted_body}"

        self.body_edit.setText(body)
        self.body_edit.moveCursor(self.body_edit.textCursor().Start)

    def setup_forward(self, message: Message):
        """Set up the window for forwarding a message."""
        self._reply_message = message

        self.setWindowTitle(f"Fwd: {message.subject}")

        subject = message.subject
        if not subject.lower().startswith("fwd:"):
            subject = f"Fwd: {subject}"
        self.subject_edit.setText(subject)

        original_date = ""
        if message.date:
            original_date = message.date.strftime("%B %d, %Y at %I:%M %p")

        original_from = str(message.from_addr) if message.from_addr else "Unknown"
        original_to = ", ".join(str(a) for a in message.to_addrs)

        original_text = message.text_body or self._html_to_plain(message.html_body)

        body = f"\n\n\n---------- Forwarded message ---------\n"
        body += f"From: {original_from}\n"
        body += f"Date: {original_date}\n"
        body += f"Subject: {message.subject}\n"
        body += f"To: {original_to}\n\n"
        body += original_text

        self.body_edit.setText(body)
        self.body_edit.moveCursor(self.body_edit.textCursor().Start)

        for attachment in message.attachments:
            self.attachment_selector.add_existing_attachment(attachment)

    def _html_to_plain(self, html: str) -> str:
        """Convert HTML to plain text (simple conversion)."""
        if not html:
            return ""

        import re
        text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
        text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)

        import html as html_module
        text = html_module.unescape(text)

        return text.strip()

    def _on_attach(self):
        """Handle attach button click."""
        self.attachment_selector._add_attachment()

    def _on_send(self):
        """Handle send button click."""
        to_text = self.to_edit.text().strip()
        if not to_text:
            QMessageBox.warning(self, "Error", "Please enter at least one recipient.")
            return

        to_list = [addr.strip() for addr in to_text.split(",") if addr.strip()]

        cc_text = self.cc_edit.text().strip()
        cc_list = [addr.strip() for addr in cc_text.split(",") if addr.strip()] if cc_text else None

        bcc_text = self.bcc_edit.text().strip()
        bcc_list = [addr.strip() for addr in bcc_text.split(",") if addr.strip()] if bcc_text else None

        subject = self.subject_edit.text()
        body = self.body_edit.toPlainText()

        attachments = self.attachment_selector.get_attachments()

        in_reply_to = None
        references = None
        if self._reply_message:
            in_reply_to = self._reply_message.message_id
            references = self._reply_message.message_id

        self.status_label.setText("Sending...")
        self._set_ui_enabled(False)

        self._worker = SendMessageWorker(
            account=self.account,
            to=to_list,
            subject=subject,
            body=body,
            cc=cc_list,
            bcc=bcc_list,
            in_reply_to=in_reply_to,
            references=references,
            attachments=attachments if attachments else None,
        )
        self._worker.signals.result.connect(self._on_send_success)
        self._worker.signals.error.connect(self._on_send_error)
        self._worker.start()

    def _on_send_success(self):
        """Handle successful send."""
        self.message_sent.emit()
        self.close()

    def _on_send_error(self, error: str):
        """Handle send error."""
        self.status_label.setText("Ready")
        self._set_ui_enabled(True)
        QMessageBox.critical(
            self,
            "Send Error",
            f"Failed to send message:\n\n{error}",
        )

    def _set_ui_enabled(self, enabled: bool):
        """Enable or disable UI elements."""
        self.to_edit.setEnabled(enabled)
        self.cc_edit.setEnabled(enabled)
        self.bcc_edit.setEnabled(enabled)
        self.subject_edit.setEnabled(enabled)
        self.body_edit.setEnabled(enabled)

    def closeEvent(self, event):
        """Handle window close."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(1000)

        body = self.body_edit.toPlainText().strip()
        has_content = bool(
            body
            and body != "\n\n\n"
            and not body.startswith("On ")
            and not body.startswith("---------- Forwarded")
        )

        if has_content:
            result = QMessageBox.question(
                self,
                "Discard Draft?",
                "You have unsent content. Discard this draft?",
                QMessageBox.Discard | QMessageBox.Cancel,
            )
            if result == QMessageBox.Cancel:
                event.ignore()
                return

        event.accept()
