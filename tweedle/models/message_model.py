"""Qt model for message list."""

from typing import Optional, Any
from datetime import datetime
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont, QColor

from tweedle.core.message import MessageHeader


class MessageModel(QAbstractTableModel):
    """Model for message list view."""

    COLUMNS = ["From", "Subject", "Date"]
    COL_FROM = 0
    COL_SUBJECT = 1
    COL_DATE = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._messages: list[MessageHeader] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._messages)

    def columnCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None

        if index.row() >= len(self._messages):
            return None

        message = self._messages[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == self.COL_FROM:
                return message.from_addr
            elif col == self.COL_SUBJECT:
                return message.subject
            elif col == self.COL_DATE:
                return message.display_date

        elif role == Qt.FontRole:
            font = QFont()
            if not message.is_read:
                font.setBold(True)
            return font

        elif role == Qt.ForegroundRole:
            if message.is_read:
                return QColor(128, 128, 128)

        elif role == Qt.UserRole:
            return message.uid

        elif role == Qt.UserRole + 1:
            return message

        elif role == Qt.DecorationRole:
            if col == self.COL_SUBJECT and message.is_flagged:
                pass

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.DisplayRole,
    ) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return None

    def set_messages(self, messages: list[MessageHeader]):
        """Replace all messages."""
        self.beginResetModel()
        self._messages = messages
        self.endResetModel()

    def append_messages(self, messages: list[MessageHeader]):
        """Append messages to the list."""
        if not messages:
            return

        start_row = len(self._messages)
        end_row = start_row + len(messages) - 1

        self.beginInsertRows(QModelIndex(), start_row, end_row)
        self._messages.extend(messages)
        self.endInsertRows()

    def clear(self):
        """Clear all messages."""
        self.beginResetModel()
        self._messages.clear()
        self.endResetModel()

    def get_message(self, index: QModelIndex) -> Optional[MessageHeader]:
        """Get a message by index."""
        if index.isValid() and 0 <= index.row() < len(self._messages):
            return self._messages[index.row()]
        return None

    def get_message_by_uid(self, uid: int) -> Optional[MessageHeader]:
        """Get a message by UID."""
        for msg in self._messages:
            if msg.uid == uid:
                return msg
        return None

    def get_uid(self, index: QModelIndex) -> Optional[int]:
        """Get the UID for an index."""
        if index.isValid() and 0 <= index.row() < len(self._messages):
            return self._messages[index.row()].uid
        return None

    def update_message_flags(self, uid: int, flags: set[str]):
        """Update flags for a message."""
        for i, msg in enumerate(self._messages):
            if msg.uid == uid:
                msg.flags = flags
                top_left = self.index(i, 0)
                bottom_right = self.index(i, len(self.COLUMNS) - 1)
                self.dataChanged.emit(top_left, bottom_right)
                break

    def remove_message(self, uid: int):
        """Remove a message by UID."""
        for i, msg in enumerate(self._messages):
            if msg.uid == uid:
                self.beginRemoveRows(QModelIndex(), i, i)
                self._messages.pop(i)
                self.endRemoveRows()
                break

    def remove_messages(self, uids: list[int]):
        """Remove multiple messages by UID."""
        uid_set = set(uids)
        rows_to_remove = [
            i for i, msg in enumerate(self._messages) if msg.uid in uid_set
        ]

        for row in sorted(rows_to_remove, reverse=True):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._messages.pop(row)
            self.endRemoveRows()

    @property
    def messages(self) -> list[MessageHeader]:
        """Get all messages."""
        return self._messages

    def get_selected_uids(self, indexes: list[QModelIndex]) -> list[int]:
        """Get UIDs for selected indexes."""
        rows = set(idx.row() for idx in indexes)
        return [
            self._messages[row].uid
            for row in rows
            if 0 <= row < len(self._messages)
        ]
