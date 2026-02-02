"""Search bar widget."""

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeySequence, QShortcut


class SearchBar(QWidget):
    """Search bar for searching messages."""

    search_requested = Signal(str)
    search_cleared = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search messages...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_edit, 1)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._on_search)
        layout.addWidget(self.search_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._on_clear)
        layout.addWidget(self.clear_button)

        shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        shortcut.activated.connect(self._focus_search)

        escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self.search_edit)
        escape_shortcut.activated.connect(self._on_clear)

    def _focus_search(self):
        """Focus the search input."""
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def _on_search(self):
        """Handle search request."""
        query = self.search_edit.text().strip()
        if query:
            self.search_requested.emit(query)

    def _on_clear(self):
        """Handle clear request."""
        self.search_edit.clear()
        self.search_cleared.emit()

    def set_query(self, query: str):
        """Set the search query."""
        self.search_edit.setText(query)

    def get_query(self) -> str:
        """Get the current search query."""
        return self.search_edit.text().strip()
