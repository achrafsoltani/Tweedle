"""Email message viewer with HTML support."""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QToolBar,
    QScrollArea,
    QFrame,
    QPushButton,
)
from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage

from tweedle.core.message import Message
from tweedle.utils.html_sanitizer import sanitize_html, text_to_html, wrap_html_document
from tweedle.ui.attachment_widget import AttachmentBar


class ExternalLinkPage(QWebEnginePage):
    """Web page that opens links externally."""

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if nav_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)


class MessageHeader(QFrame):
    """Widget displaying message header info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        self.subject_label = QLabel()
        self.subject_label.setWordWrap(True)
        font = self.subject_label.font()
        font.setPointSize(font.pointSize() + 2)
        font.setBold(True)
        self.subject_label.setFont(font)
        layout.addWidget(self.subject_label)

        self.from_label = QLabel()
        self.from_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.from_label)

        self.to_label = QLabel()
        self.to_label.setWordWrap(True)
        self.to_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.to_label)

        self.cc_label = QLabel()
        self.cc_label.setWordWrap(True)
        self.cc_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.cc_label.setVisible(False)
        layout.addWidget(self.cc_label)

        self.date_label = QLabel()
        self.date_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.date_label)

    def set_message(self, message: Message):
        """Display message header information."""
        self.subject_label.setText(message.subject or "(No subject)")

        if message.from_addr:
            self.from_label.setText(f"From: {message.from_addr}")
        else:
            self.from_label.setText("From: (unknown)")

        to_str = ", ".join(str(addr) for addr in message.to_addrs)
        self.to_label.setText(f"To: {to_str}")

        if message.cc_addrs:
            cc_str = ", ".join(str(addr) for addr in message.cc_addrs)
            self.cc_label.setText(f"Cc: {cc_str}")
            self.cc_label.setVisible(True)
        else:
            self.cc_label.setVisible(False)

        if message.date:
            date_str = message.date.strftime("%A, %B %d, %Y at %I:%M %p")
            self.date_label.setText(f"Date: {date_str}")
        else:
            self.date_label.setText("Date: (unknown)")

    def clear(self):
        """Clear the header display."""
        self.subject_label.setText("")
        self.from_label.setText("")
        self.to_label.setText("")
        self.cc_label.setText("")
        self.cc_label.setVisible(False)
        self.date_label.setText("")


class MessageView(QWidget):
    """Widget for viewing email messages."""

    reply_requested = Signal()
    reply_all_requested = Signal()
    forward_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_message: Optional[Message] = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QToolBar()
        toolbar.setMovable(False)

        reply_action = QAction("Reply", self)
        reply_action.triggered.connect(self.reply_requested.emit)
        toolbar.addAction(reply_action)

        reply_all_action = QAction("Reply All", self)
        reply_all_action.triggered.connect(self.reply_all_requested.emit)
        toolbar.addAction(reply_all_action)

        forward_action = QAction("Forward", self)
        forward_action.triggered.connect(self.forward_requested.emit)
        toolbar.addAction(forward_action)

        layout.addWidget(toolbar)

        self.header_widget = MessageHeader()
        layout.addWidget(self.header_widget)

        self.attachment_bar = AttachmentBar()
        self.attachment_bar.setVisible(False)
        layout.addWidget(self.attachment_bar)

        self.web_view = QWebEngineView()
        self.web_view.setPage(ExternalLinkPage(self.web_view))
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)
        layout.addWidget(self.web_view)

        self._show_empty_state()

    def _show_empty_state(self):
        """Show empty state when no message is selected."""
        html = """
        <html>
        <head>
            <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    font-family: sans-serif;
                    color: #888;
                    background: #fafafa;
                }
            </style>
        </head>
        <body>
            <p>Select a message to view</p>
        </body>
        </html>
        """
        self.web_view.setHtml(html)

    def display_message(self, message: Message):
        """Display an email message."""
        self._current_message = message

        self.header_widget.set_message(message)

        if message.attachments:
            self.attachment_bar.set_attachments(message.attachments)
            self.attachment_bar.setVisible(True)
        else:
            self.attachment_bar.setVisible(False)

        if message.html_body:
            sanitized = sanitize_html(message.html_body)
            html = wrap_html_document(sanitized, message.subject)
        else:
            html_body = text_to_html(message.text_body)
            html = wrap_html_document(html_body, message.subject)

        self.web_view.setHtml(html)

    def clear(self):
        """Clear the message view."""
        self._current_message = None
        self.header_widget.clear()
        self.attachment_bar.setVisible(False)
        self._show_empty_state()

    @property
    def current_message(self) -> Optional[Message]:
        """Get the currently displayed message."""
        return self._current_message
