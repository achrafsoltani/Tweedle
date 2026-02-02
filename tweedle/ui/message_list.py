"""Message list view widget."""

from typing import Optional
from PySide6.QtWidgets import (
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QMenu,
)
from PySide6.QtCore import Signal, Qt, QModelIndex

from tweedle.models.message_model import MessageModel
from tweedle.core.message import MessageHeader


class MessageList(QTableView):
    """Table view for email message list."""

    message_selected = Signal(int)
    messages_deleted = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = MessageModel()
        self.setModel(self._model)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        self.setShowGrid(False)

        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(28)

        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.setColumnWidth(0, 200)
        self.setColumnWidth(2, 80)

        self.clicked.connect(self._on_clicked)
        self.activated.connect(self._on_clicked)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def _on_clicked(self, index: QModelIndex):
        """Handle message click."""
        uid = self._model.get_uid(index)
        if uid is not None:
            self.message_selected.emit(uid)

    def _on_context_menu(self, pos):
        """Show context menu."""
        indexes = self.selectedIndexes()
        if not indexes:
            return

        uids = self._model.get_selected_uids(indexes)
        if not uids:
            return

        menu = QMenu(self)

        mark_read = menu.addAction("Mark as Read")
        mark_unread = menu.addAction("Mark as Unread")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        action = menu.exec(self.viewport().mapToGlobal(pos))

        if action == delete_action:
            self.messages_deleted.emit(uids)
        elif action == mark_read:
            self.update_flags(uids, {"\\Seen"}, add=True)
        elif action == mark_unread:
            self.update_flags(uids, {"\\Seen"}, add=False)

    def set_messages(self, messages: list[MessageHeader]):
        """Set the message list."""
        self._model.set_messages(messages)

    def append_messages(self, messages: list[MessageHeader]):
        """Append messages to the list."""
        self._model.append_messages(messages)

    def clear(self):
        """Clear the message list."""
        self._model.clear()

    def get_selected_uids(self) -> list[int]:
        """Get UIDs of selected messages."""
        return self._model.get_selected_uids(self.selectedIndexes())

    def update_flags(self, uids: list[int], flags: set[str], add: bool = True):
        """Update flags for messages."""
        for uid in uids:
            msg = self._model.get_message_by_uid(uid)
            if msg:
                if add:
                    new_flags = msg.flags | flags
                else:
                    new_flags = msg.flags - flags
                self._model.update_message_flags(uid, new_flags)

    def remove_messages(self, uids: list[int]):
        """Remove messages from the list."""
        self._model.remove_messages(uids)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Delete:
            uids = self.get_selected_uids()
            if uids:
                self.messages_deleted.emit(uids)
        else:
            super().keyPressEvent(event)
