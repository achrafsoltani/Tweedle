"""Main application window."""

from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QToolBar,
    QStatusBar,
    QMessageBox,
    QLabel,
    QComboBox,
    QMenu,
    QMenuBar,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence

from tweedle.core.account import Account, account_manager
from tweedle.core.imap_client import IMAPClientWrapper
from tweedle.core.workers import (
    ConnectWorker,
    FetchFoldersWorker,
    FetchMessagesWorker,
    FetchMessageWorker,
    DeleteMessagesWorker,
    ModifyFlagsWorker,
)
from tweedle.ui.folder_tree import FolderTree
from tweedle.ui.message_list import MessageList
from tweedle.ui.message_view import MessageView
from tweedle.ui.account_dialog import AccountDialog
from tweedle.ui.compose_window import ComposeWindow
from tweedle.ui.search_bar import SearchBar
from tweedle.utils.config import config_manager


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tweedle")
        self.resize(
            config_manager.config.window_width,
            config_manager.config.window_height,
        )

        self._current_account: Optional[Account] = None
        self._imap_client: Optional[IMAPClientWrapper] = None
        self._current_folder: Optional[str] = None
        self._workers = []

        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._setup_shortcuts()

        account_manager.load_accounts()
        self._update_account_selector()

        if account_manager.accounts:
            self._switch_account(account_manager.accounts[0])

    def _setup_ui(self):
        """Set up the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.search_bar = SearchBar()
        self.search_bar.search_requested.connect(self._on_search)
        self.search_bar.search_cleared.connect(self._on_search_cleared)
        layout.addWidget(self.search_bar)

        main_splitter = QSplitter(Qt.Horizontal)

        self.folder_tree = FolderTree()
        self.folder_tree.folder_selected.connect(self._on_folder_selected)
        main_splitter.addWidget(self.folder_tree)

        right_splitter = QSplitter(Qt.Vertical)

        self.message_list = MessageList()
        self.message_list.message_selected.connect(self._on_message_selected)
        self.message_list.messages_deleted.connect(self._on_messages_deleted)
        right_splitter.addWidget(self.message_list)

        self.message_view = MessageView()
        self.message_view.reply_requested.connect(self._on_reply)
        self.message_view.reply_all_requested.connect(self._on_reply_all)
        self.message_view.forward_requested.connect(self._on_forward)
        right_splitter.addWidget(self.message_view)

        right_splitter.setSizes([
            config_manager.config.message_list_height,
            config_manager.config.window_height - config_manager.config.message_list_height,
        ])

        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([
            config_manager.config.sidebar_width,
            config_manager.config.window_width - config_manager.config.sidebar_width,
        ])

        layout.addWidget(main_splitter)

    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New Message", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._on_compose)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        add_account_action = QAction("&Add Account...", self)
        add_account_action.triggered.connect(self._on_add_account)
        file_menu.addAction(add_account_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        edit_menu = menubar.addMenu("&Edit")

        self.mark_read_action = QAction("Mark as &Read", self)
        self.mark_read_action.setShortcut("R")
        self.mark_read_action.triggered.connect(self._on_mark_read)
        edit_menu.addAction(self.mark_read_action)

        self.mark_unread_action = QAction("Mark as &Unread", self)
        self.mark_unread_action.setShortcut("U")
        self.mark_unread_action.triggered.connect(self._on_mark_unread)
        edit_menu.addAction(self.mark_unread_action)

        edit_menu.addSeparator()

        self.delete_action = QAction("&Delete", self)
        self.delete_action.setShortcut(QKeySequence.Delete)
        self.delete_action.triggered.connect(self._on_delete)
        edit_menu.addAction(self.delete_action)

        view_menu = menubar.addMenu("&View")

        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.triggered.connect(self._on_refresh)
        view_menu.addAction(refresh_action)

        message_menu = menubar.addMenu("&Message")

        reply_action = QAction("&Reply", self)
        reply_action.setShortcut("Ctrl+R")
        reply_action.triggered.connect(self._on_reply)
        message_menu.addAction(reply_action)

        reply_all_action = QAction("Reply &All", self)
        reply_all_action.setShortcut("Ctrl+Shift+R")
        reply_all_action.triggered.connect(self._on_reply_all)
        message_menu.addAction(reply_all_action)

        forward_action = QAction("&Forward", self)
        forward_action.setShortcut("Ctrl+F")
        forward_action.triggered.connect(self._on_forward)
        message_menu.addAction(forward_action)

    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        self.account_selector = QComboBox()
        self.account_selector.setMinimumWidth(150)
        self.account_selector.currentIndexChanged.connect(self._on_account_changed)
        toolbar.addWidget(self.account_selector)

        toolbar.addSeparator()

        compose_action = QAction("Compose", self)
        compose_action.triggered.connect(self._on_compose)
        toolbar.addAction(compose_action)

        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._on_refresh)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        reply_action = QAction("Reply", self)
        reply_action.triggered.connect(self._on_reply)
        toolbar.addAction(reply_action)

        forward_action = QAction("Forward", self)
        forward_action.triggered.connect(self._on_forward)
        toolbar.addAction(forward_action)

        toolbar.addSeparator()

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._on_delete)
        toolbar.addAction(delete_action)

    def _setup_statusbar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

    def _setup_shortcuts(self):
        """Set up additional keyboard shortcuts."""
        pass

    def _update_account_selector(self):
        """Update the account selector combo box."""
        self.account_selector.blockSignals(True)
        self.account_selector.clear()

        for account in account_manager.accounts:
            self.account_selector.addItem(account.name, account.id)

        self.account_selector.blockSignals(False)

    def _switch_account(self, account: Account):
        """Switch to a different account."""
        if self._imap_client:
            try:
                self._imap_client.disconnect()
            except Exception:
                pass
            self._imap_client = None

        self._current_account = account
        self._current_folder = None

        self.folder_tree.clear()
        self.message_list.clear()
        self.message_view.clear()

        self._connect_to_account()

    def _connect_to_account(self):
        """Connect to the current account's IMAP server."""
        if not self._current_account:
            return

        self._set_status(f"Connecting to {self._current_account.config.imap_server}...")

        worker = ConnectWorker(self._current_account)
        worker.signals.result.connect(self._on_connected)
        worker.signals.error.connect(self._on_connection_error)
        self._workers.append(worker)
        worker.start()

    def _on_connected(self, client: IMAPClientWrapper):
        """Handle successful connection."""
        self._imap_client = client
        self._set_status("Connected")
        self._fetch_folders()

    def _on_connection_error(self, error: str):
        """Handle connection error."""
        self._set_status(f"Connection failed: {error}")
        QMessageBox.critical(
            self,
            "Connection Error",
            f"Failed to connect to email server:\n\n{error}",
        )

    def _fetch_folders(self):
        """Fetch folder list from server."""
        if not self._imap_client:
            return

        self._set_status("Fetching folders...")

        worker = FetchFoldersWorker(self._imap_client)
        worker.signals.result.connect(self._on_folders_fetched)
        worker.signals.error.connect(lambda e: self._set_status(f"Error: {e}"))
        self._workers.append(worker)
        worker.start()

    def _on_folders_fetched(self, folders):
        """Handle fetched folders."""
        self.folder_tree.load_folders(folders)
        self._set_status("Ready")

        inbox_index = self.folder_tree.find_folder("INBOX")
        if inbox_index and inbox_index.isValid():
            self.folder_tree.select_folder(inbox_index)

    def _on_folder_selected(self, folder_path: str):
        """Handle folder selection."""
        self._current_folder = folder_path
        self.message_list.clear()
        self.message_view.clear()
        self._fetch_messages(folder_path)

    def _fetch_messages(self, folder: str, limit: int = 50, offset: int = 0):
        """Fetch messages from the current folder."""
        if not self._imap_client:
            return

        self._set_status(f"Fetching messages from {folder}...")

        worker = FetchMessagesWorker(self._imap_client, folder, limit, offset)
        worker.signals.result.connect(self._on_messages_fetched)
        worker.signals.error.connect(lambda e: self._set_status(f"Error: {e}"))
        self._workers.append(worker)
        worker.start()

    def _on_messages_fetched(self, messages):
        """Handle fetched messages."""
        self.message_list.set_messages(messages)
        self._set_status(f"{len(messages)} messages")

    def _on_message_selected(self, uid: int):
        """Handle message selection."""
        if not self._imap_client or not self._current_folder:
            return

        self._set_status("Loading message...")

        worker = FetchMessageWorker(self._imap_client, self._current_folder, uid)
        worker.signals.result.connect(self._on_message_fetched)
        worker.signals.error.connect(lambda e: self._set_status(f"Error: {e}"))
        self._workers.append(worker)
        worker.start()

    def _on_message_fetched(self, message):
        """Handle fetched full message."""
        if message:
            self.message_view.display_message(message)
            self._set_status("Ready")

            if not message.is_read and self._imap_client and self._current_folder:
                self._mark_messages_read([message.uid])
        else:
            self._set_status("Message not found")

    def _mark_messages_read(self, uids: list[int]):
        """Mark messages as read."""
        if not self._imap_client or not self._current_folder:
            return

        worker = ModifyFlagsWorker(
            self._imap_client,
            self._current_folder,
            uids,
            "mark_read",
        )
        worker.signals.result.connect(
            lambda: self.message_list.update_flags(uids, {"\\Seen"}, add=True)
        )
        self._workers.append(worker)
        worker.start()

    def _on_messages_deleted(self, uids: list[int]):
        """Handle message deletion request."""
        if not self._imap_client or not self._current_folder:
            return

        worker = DeleteMessagesWorker(
            self._imap_client,
            self._current_folder,
            uids,
        )
        worker.signals.result.connect(lambda: self.message_list.remove_messages(uids))
        worker.signals.error.connect(lambda e: self._set_status(f"Error: {e}"))
        self._workers.append(worker)
        worker.start()

    def _on_search(self, query: str):
        """Handle search request."""
        if not self._imap_client or not self._current_folder:
            return

        from tweedle.core.workers import SearchWorker

        self._set_status(f"Searching for '{query}'...")

        worker = SearchWorker(self._imap_client, self._current_folder, query)
        worker.signals.result.connect(self._on_messages_fetched)
        worker.signals.error.connect(lambda e: self._set_status(f"Search error: {e}"))
        self._workers.append(worker)
        worker.start()

    def _on_search_cleared(self):
        """Handle search clear."""
        if self._current_folder:
            self._fetch_messages(self._current_folder)

    def _on_account_changed(self, index: int):
        """Handle account selector change."""
        if index < 0:
            return

        account_id = self.account_selector.itemData(index)
        account = account_manager.get_account(account_id)
        if account and account != self._current_account:
            self._switch_account(account)

    def _on_add_account(self):
        """Show add account dialog."""
        dialog = AccountDialog(self)
        if dialog.exec():
            account = dialog.get_account()
            if account:
                self._update_account_selector()
                idx = self.account_selector.findData(account.id)
                if idx >= 0:
                    self.account_selector.setCurrentIndex(idx)
                self._switch_account(account)

    def _on_compose(self):
        """Open compose window for new message."""
        if not self._current_account:
            QMessageBox.warning(self, "No Account", "Please add an account first.")
            return

        compose = ComposeWindow(self._current_account, parent=self)
        compose.message_sent.connect(lambda: self._set_status("Message sent"))
        compose.show()

    def _on_reply(self):
        """Reply to current message."""
        message = self.message_view.current_message
        if not message or not self._current_account:
            return

        compose = ComposeWindow(self._current_account, parent=self)
        compose.setup_reply(message, reply_all=False)
        compose.message_sent.connect(lambda: self._set_status("Reply sent"))
        compose.show()

    def _on_reply_all(self):
        """Reply all to current message."""
        message = self.message_view.current_message
        if not message or not self._current_account:
            return

        compose = ComposeWindow(self._current_account, parent=self)
        compose.setup_reply(message, reply_all=True)
        compose.message_sent.connect(lambda: self._set_status("Reply sent"))
        compose.show()

    def _on_forward(self):
        """Forward current message."""
        message = self.message_view.current_message
        if not message or not self._current_account:
            return

        compose = ComposeWindow(self._current_account, parent=self)
        compose.setup_forward(message)
        compose.message_sent.connect(lambda: self._set_status("Message forwarded"))
        compose.show()

    def _on_mark_read(self):
        """Mark selected messages as read."""
        uids = self.message_list.get_selected_uids()
        if uids:
            self._mark_messages_read(uids)

    def _on_mark_unread(self):
        """Mark selected messages as unread."""
        if not self._imap_client or not self._current_folder:
            return

        uids = self.message_list.get_selected_uids()
        if not uids:
            return

        worker = ModifyFlagsWorker(
            self._imap_client,
            self._current_folder,
            uids,
            "mark_unread",
        )
        worker.signals.result.connect(
            lambda: self.message_list.update_flags(uids, {"\\Seen"}, add=False)
        )
        self._workers.append(worker)
        worker.start()

    def _on_delete(self):
        """Delete selected messages."""
        uids = self.message_list.get_selected_uids()
        if uids:
            self._on_messages_deleted(uids)

    def _on_refresh(self):
        """Refresh current folder."""
        if self._current_folder:
            self._fetch_messages(self._current_folder)
        elif self._imap_client:
            self._fetch_folders()

    def _set_status(self, message: str):
        """Update status bar message."""
        self.status_label.setText(message)

    def closeEvent(self, event):
        """Handle window close."""
        for worker in self._workers:
            if worker.isRunning():
                worker.cancel()
                worker.wait(1000)

        if self._imap_client:
            try:
                self._imap_client.disconnect()
            except Exception:
                pass

        config = config_manager.config
        config.window_width = self.width()
        config.window_height = self.height()
        config_manager.save()

        event.accept()
