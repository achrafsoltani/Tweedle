"""Folder tree navigation widget."""

from typing import Optional
from PySide6.QtWidgets import QTreeView, QAbstractItemView
from PySide6.QtCore import Signal, QModelIndex

from tweedle.models.folder_model import FolderModel


class FolderTree(QTreeView):
    """Tree view for email folders."""

    folder_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = FolderModel()
        self.setModel(self._model)

        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setAnimated(True)
        self.setExpandsOnDoubleClick(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.setMinimumWidth(150)
        self.setMaximumWidth(300)

        self.clicked.connect(self._on_clicked)
        self.activated.connect(self._on_clicked)

    def _on_clicked(self, index: QModelIndex):
        """Handle folder click."""
        folder_path = self._model.get_folder_path(index)
        if folder_path:
            self.folder_selected.emit(folder_path)

    def load_folders(self, folders: list[tuple[str, str, int, int]]):
        """Load folders into the tree."""
        self._model.load_folders(folders)
        self.expandAll()

    def clear(self):
        """Clear the folder tree."""
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["Folders"])

    def find_folder(self, folder_path: str) -> Optional[QModelIndex]:
        """Find a folder by path."""
        return self._model.find_folder_index(folder_path)

    def select_folder(self, index: QModelIndex):
        """Select a folder by index."""
        if index and index.isValid():
            self.setCurrentIndex(index)
            self._on_clicked(index)

    def update_folder_counts(self, folder_path: str, total: int, unread: int):
        """Update message counts for a folder."""
        self._model.update_folder_counts(folder_path, total, unread)
