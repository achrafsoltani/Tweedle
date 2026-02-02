"""Qt model for folder tree."""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtWidgets import QStyle, QApplication


class FolderItem(QStandardItem):
    """Custom item for folder tree."""

    def __init__(self, name: str, full_path: str, unread: int = 0, total: int = 0):
        super().__init__(name)
        self.full_path = full_path
        self.unread = unread
        self.total = total
        self._update_display()

    def _update_display(self):
        """Update the display text with unread count."""
        if self.unread > 0:
            self.setText(f"{self.text().split(' (')[0]} ({self.unread})")
            font = self.font()
            font.setBold(True)
            self.setFont(font)

    def set_counts(self, total: int, unread: int):
        """Update message counts."""
        self.total = total
        self.unread = unread
        base_name = self.text().split(" (")[0]
        if unread > 0:
            self.setText(f"{base_name} ({unread})")
            font = self.font()
            font.setBold(True)
            self.setFont(font)
        else:
            self.setText(base_name)
            font = self.font()
            font.setBold(False)
            self.setFont(font)


class FolderModel(QStandardItemModel):
    """Model for folder tree view."""

    STANDARD_FOLDERS = {
        "INBOX": ("Inbox", "mail-inbox"),
        "Sent": ("Sent", "mail-sent"),
        "Sent Messages": ("Sent", "mail-sent"),
        "Sent Items": ("Sent", "mail-sent"),
        "[Gmail]/Sent Mail": ("Sent", "mail-sent"),
        "Drafts": ("Drafts", "mail-drafts"),
        "[Gmail]/Drafts": ("Drafts", "mail-drafts"),
        "Trash": ("Trash", "user-trash"),
        "Deleted Items": ("Trash", "user-trash"),
        "[Gmail]/Trash": ("Trash", "user-trash"),
        "Spam": ("Spam", "mail-mark-junk"),
        "Junk": ("Spam", "mail-mark-junk"),
        "[Gmail]/Spam": ("Spam", "mail-mark-junk"),
        "Archive": ("Archive", "mail-archive"),
        "[Gmail]/All Mail": ("All Mail", "mail-archive"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalHeaderLabels(["Folders"])
        self._folder_items: dict[str, FolderItem] = {}

    def load_folders(self, folders: list[tuple[str, str, int, int]]):
        """
        Load folders into the model.

        Args:
            folders: List of (name, delimiter, total, unread) tuples
        """
        self.clear()
        self.setHorizontalHeaderLabels(["Folders"])
        self._folder_items.clear()

        standard_order = ["INBOX", "Drafts", "Sent", "Trash", "Spam", "Archive"]
        standard_folders = []
        other_folders = []

        for name, delimiter, total, unread in folders:
            display_name = name
            icon_name = "folder"

            if name in self.STANDARD_FOLDERS:
                display_name, icon_name = self.STANDARD_FOLDERS[name]
                standard_folders.append((name, display_name, icon_name, total, unread, delimiter))
            else:
                for std_name, (std_display, std_icon) in self.STANDARD_FOLDERS.items():
                    if name.lower() == std_name.lower() or name.endswith(f"/{std_name}"):
                        display_name = std_display
                        icon_name = std_icon
                        standard_folders.append((name, display_name, icon_name, total, unread, delimiter))
                        break
                else:
                    other_folders.append((name, display_name, icon_name, total, unread, delimiter))

        def sort_key(f):
            name = f[1]
            for i, std in enumerate(standard_order):
                if name.lower() == std.lower():
                    return (0, i)
            return (1, f[0].lower())

        standard_folders.sort(key=sort_key)

        for full_path, display_name, icon_name, total, unread, delimiter in standard_folders:
            self._add_folder_item(full_path, display_name, total, unread)

        other_folders.sort(key=lambda f: f[0].lower())

        for full_path, display_name, icon_name, total, unread, delimiter in other_folders:
            if delimiter and delimiter in full_path:
                parts = full_path.split(delimiter)
                if len(parts) > 1:
                    self._add_nested_folder(parts, delimiter, full_path, total, unread)
                    continue
            self._add_folder_item(full_path, display_name, total, unread)

    def _add_folder_item(
        self,
        full_path: str,
        display_name: str,
        total: int,
        unread: int,
        parent: Optional[QStandardItem] = None,
    ) -> FolderItem:
        """Add a folder item to the model."""
        item = FolderItem(display_name, full_path, unread, total)
        item.setEditable(False)

        if parent:
            parent.appendRow(item)
        else:
            self.appendRow(item)

        self._folder_items[full_path] = item
        return item

    def _add_nested_folder(
        self,
        parts: list[str],
        delimiter: str,
        full_path: str,
        total: int,
        unread: int,
    ):
        """Add a nested folder structure."""
        parent = None
        current_path = ""

        for i, part in enumerate(parts):
            if current_path:
                current_path = f"{current_path}{delimiter}{part}"
            else:
                current_path = part

            if current_path in self._folder_items:
                parent = self._folder_items[current_path]
            else:
                is_last = i == len(parts) - 1
                if is_last:
                    parent = self._add_folder_item(full_path, part, total, unread, parent)
                else:
                    parent = self._add_folder_item(current_path, part, 0, 0, parent)

    def get_folder_path(self, index) -> Optional[str]:
        """Get the full folder path for an index."""
        item = self.itemFromIndex(index)
        if isinstance(item, FolderItem):
            return item.full_path
        return None

    def update_folder_counts(self, folder_path: str, total: int, unread: int):
        """Update message counts for a folder."""
        if folder_path in self._folder_items:
            self._folder_items[folder_path].set_counts(total, unread)

    def find_folder_index(self, folder_path: str):
        """Find the index of a folder by path."""
        if folder_path in self._folder_items:
            return self._folder_items[folder_path].index()
        return None
