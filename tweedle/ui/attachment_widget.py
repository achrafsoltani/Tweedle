"""Attachment handling widgets."""

import os
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QScrollArea,
    QFrame,
    QMenu,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction

from tweedle.core.message import Attachment


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


class AttachmentButton(QPushButton):
    """Button representing a single attachment."""

    save_requested = Signal(object)

    def __init__(self, attachment: Attachment, parent=None):
        super().__init__(parent)
        self.attachment = attachment

        size_str = format_size(attachment.size)
        self.setText(f"{attachment.filename} ({size_str})")

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self.clicked.connect(lambda: self.save_requested.emit(self.attachment))

    def _show_context_menu(self, pos):
        """Show context menu for attachment."""
        menu = QMenu(self)

        save_action = menu.addAction("Save As...")
        save_action.triggered.connect(lambda: self.save_requested.emit(self.attachment))

        menu.exec(self.mapToGlobal(pos))


class AttachmentBar(QWidget):
    """Widget displaying message attachments."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._attachments: list[Attachment] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        self.label = QLabel("Attachments:")
        layout.addWidget(self.label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setMaximumHeight(40)

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(5)
        self.button_layout.addStretch()

        self.scroll_area.setWidget(self.button_container)
        layout.addWidget(self.scroll_area, 1)

    def set_attachments(self, attachments: list[Attachment]):
        """Set the attachments to display."""
        self._attachments = attachments

        while self.button_layout.count() > 1:
            item = self.button_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for attachment in attachments:
            btn = AttachmentButton(attachment)
            btn.save_requested.connect(self._save_attachment)
            self.button_layout.insertWidget(self.button_layout.count() - 1, btn)

    def _save_attachment(self, attachment: Attachment):
        """Save an attachment to disk."""
        default_path = str(Path.home() / attachment.filename)
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Attachment",
            default_path,
            "All Files (*)",
        )

        if filepath:
            try:
                with open(filepath, "wb") as f:
                    f.write(attachment.data)
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to save attachment:\n{e}",
                )


class AttachmentSelector(QWidget):
    """Widget for selecting attachments when composing."""

    attachments_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._attachments: list[tuple[str, bytes, str]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Attachment")
        self.add_button.clicked.connect(self._add_attachment)
        button_layout.addWidget(self.add_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(2)
        layout.addWidget(self.list_widget)

    def _add_attachment(self):
        """Add an attachment from file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Attachment",
            str(Path.home()),
            "All Files (*)",
        )

        if filepath:
            from tweedle.core.smtp_client import load_attachment_from_file
            try:
                attachment = load_attachment_from_file(filepath)
                self._attachments.append(attachment)
                self._update_list()
                self.attachments_changed.emit()
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load attachment:\n{e}",
                )

    def _update_list(self):
        """Update the attachment list display."""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, (filename, data, _) in enumerate(self._attachments):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            size_str = format_size(len(data))
            label = QLabel(f"{filename} ({size_str})")
            row_layout.addWidget(label, 1)

            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, idx=i: self._remove_attachment(idx))
            row_layout.addWidget(remove_btn)

            self.list_layout.addWidget(row)

    def _remove_attachment(self, index: int):
        """Remove an attachment by index."""
        if 0 <= index < len(self._attachments):
            self._attachments.pop(index)
            self._update_list()
            self.attachments_changed.emit()

    def get_attachments(self) -> list[tuple[str, bytes, str]]:
        """Get the list of attachments."""
        return self._attachments

    def add_existing_attachment(self, attachment: Attachment):
        """Add an existing attachment (for forwarding)."""
        self._attachments.append((
            attachment.filename,
            attachment.data,
            attachment.content_type,
        ))
        self._update_list()
        self.attachments_changed.emit()

    def clear(self):
        """Clear all attachments."""
        self._attachments.clear()
        self._update_list()
