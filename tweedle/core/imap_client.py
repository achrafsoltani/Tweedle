"""IMAP client for email operations."""

import ssl
from typing import Optional, Callable
from imapclient import IMAPClient

from tweedle.core.account import Account
from tweedle.core.message import (
    Message,
    MessageHeader,
    parse_message,
    parse_message_header,
)


class IMAPClientWrapper:
    """Wrapper around IMAPClient for email operations."""

    def __init__(self, account: Account):
        self.account = account
        self._client: Optional[IMAPClient] = None
        self._current_folder: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    def connect(self) -> bool:
        """Connect to the IMAP server."""
        try:
            config = self.account.config
            ssl_context = ssl.create_default_context() if config.imap_ssl else None

            self._client = IMAPClient(
                config.imap_server,
                port=config.imap_port,
                ssl=config.imap_ssl,
                ssl_context=ssl_context,
            )

            password = self.account.password
            if not password:
                raise ValueError("No password available")

            self._client.login(config.email, password)
            return True
        except Exception as e:
            self._client = None
            raise ConnectionError(f"Failed to connect: {e}")

    def disconnect(self) -> None:
        """Disconnect from the IMAP server."""
        if self._client:
            try:
                self._client.logout()
            except Exception:
                pass
            self._client = None
            self._current_folder = None

    def list_folders(self) -> list[tuple[str, str]]:
        """List all folders. Returns list of (name, delimiter) tuples."""
        if not self._client:
            raise ConnectionError("Not connected")

        folders = []
        for flags, delimiter, name in self._client.list_folders():
            if isinstance(delimiter, bytes):
                delimiter = delimiter.decode("utf-8")
            if isinstance(name, bytes):
                name = name.decode("utf-8")
            folders.append((name, delimiter))
        return folders

    def select_folder(self, folder: str, readonly: bool = False) -> dict:
        """Select a folder for operations."""
        if not self._client:
            raise ConnectionError("Not connected")

        result = self._client.select_folder(folder, readonly=readonly)
        self._current_folder = folder
        return result

    def get_message_count(self, folder: str) -> tuple[int, int]:
        """Get (total, unread) message count for a folder."""
        if not self._client:
            raise ConnectionError("Not connected")

        status = self._client.folder_status(folder, ["MESSAGES", "UNSEEN"])
        total = status.get(b"MESSAGES", 0)
        unread = status.get(b"UNSEEN", 0)
        return (total, unread)

    def fetch_message_headers(
        self,
        folder: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MessageHeader]:
        """Fetch message headers from a folder."""
        if not self._client:
            raise ConnectionError("Not connected")

        self.select_folder(folder, readonly=True)

        messages = self._client.search(["ALL"])
        if not messages:
            return []

        messages = sorted(messages, reverse=True)

        if offset:
            messages = messages[offset:]
        if limit:
            messages = messages[:limit]

        if not messages:
            return []

        fetch_data = self._client.fetch(messages, ["ENVELOPE", "FLAGS"])

        headers = []
        for uid, data in fetch_data.items():
            envelope = data.get(b"ENVELOPE")
            flags = set(
                f.decode("utf-8") if isinstance(f, bytes) else f
                for f in data.get(b"FLAGS", [])
            )

            if envelope:
                header = parse_message_header(uid, envelope, flags)
                headers.append(header)

        headers.sort(key=lambda h: h.date or "", reverse=True)
        return headers

    def fetch_message(self, folder: str, uid: int) -> Optional[Message]:
        """Fetch a complete message by UID."""
        if not self._client:
            raise ConnectionError("Not connected")

        if self._current_folder != folder:
            self.select_folder(folder, readonly=True)

        fetch_data = self._client.fetch([uid], ["RFC822", "FLAGS"])

        if uid not in fetch_data:
            return None

        data = fetch_data[uid]
        raw_message = data.get(b"RFC822", b"")
        flags = set(
            f.decode("utf-8") if isinstance(f, bytes) else f
            for f in data.get(b"FLAGS", [])
        )

        return parse_message(uid, raw_message, flags, folder)

    def search(
        self,
        folder: str,
        query: str,
        limit: int = 50,
    ) -> list[MessageHeader]:
        """Search messages in a folder."""
        if not self._client:
            raise ConnectionError("Not connected")

        self.select_folder(folder, readonly=True)

        criteria = ["OR", "OR",
            "SUBJECT", query,
            "FROM", query,
            "BODY", query,
        ]

        try:
            messages = self._client.search(criteria)
        except Exception:
            messages = self._client.search(["TEXT", query])

        if not messages:
            return []

        messages = sorted(messages, reverse=True)[:limit]

        fetch_data = self._client.fetch(messages, ["ENVELOPE", "FLAGS"])

        headers = []
        for uid, data in fetch_data.items():
            envelope = data.get(b"ENVELOPE")
            flags = set(
                f.decode("utf-8") if isinstance(f, bytes) else f
                for f in data.get(b"FLAGS", [])
            )

            if envelope:
                header = parse_message_header(uid, envelope, flags)
                headers.append(header)

        headers.sort(key=lambda h: h.date or "", reverse=True)
        return headers

    def mark_read(self, folder: str, uids: list[int]) -> None:
        """Mark messages as read."""
        if not self._client:
            raise ConnectionError("Not connected")

        if self._current_folder != folder:
            self.select_folder(folder)

        self._client.add_flags(uids, ["\\Seen"])

    def mark_unread(self, folder: str, uids: list[int]) -> None:
        """Mark messages as unread."""
        if not self._client:
            raise ConnectionError("Not connected")

        if self._current_folder != folder:
            self.select_folder(folder)

        self._client.remove_flags(uids, ["\\Seen"])

    def mark_flagged(self, folder: str, uids: list[int]) -> None:
        """Flag messages."""
        if not self._client:
            raise ConnectionError("Not connected")

        if self._current_folder != folder:
            self.select_folder(folder)

        self._client.add_flags(uids, ["\\Flagged"])

    def mark_unflagged(self, folder: str, uids: list[int]) -> None:
        """Unflag messages."""
        if not self._client:
            raise ConnectionError("Not connected")

        if self._current_folder != folder:
            self.select_folder(folder)

        self._client.remove_flags(uids, ["\\Flagged"])

    def move_messages(self, folder: str, uids: list[int], dest_folder: str) -> None:
        """Move messages to another folder."""
        if not self._client:
            raise ConnectionError("Not connected")

        if self._current_folder != folder:
            self.select_folder(folder)

        self._client.move(uids, dest_folder)

    def delete_messages(self, folder: str, uids: list[int]) -> None:
        """Delete messages (move to trash or mark deleted)."""
        if not self._client:
            raise ConnectionError("Not connected")

        if self._current_folder != folder:
            self.select_folder(folder)

        trash_folders = ["Trash", "[Gmail]/Trash", "Deleted Items", "Deleted"]
        target_trash = None

        folders = self.list_folders()
        folder_names = [f[0] for f in folders]

        for trash in trash_folders:
            if trash in folder_names:
                target_trash = trash
                break

        if target_trash and folder != target_trash:
            self._client.move(uids, target_trash)
        else:
            self._client.add_flags(uids, ["\\Deleted"])
            self._client.expunge()

    def copy_messages(self, folder: str, uids: list[int], dest_folder: str) -> None:
        """Copy messages to another folder."""
        if not self._client:
            raise ConnectionError("Not connected")

        if self._current_folder != folder:
            self.select_folder(folder)

        self._client.copy(uids, dest_folder)

    def create_folder(self, folder: str) -> None:
        """Create a new folder."""
        if not self._client:
            raise ConnectionError("Not connected")

        self._client.create_folder(folder)

    def delete_folder(self, folder: str) -> None:
        """Delete a folder."""
        if not self._client:
            raise ConnectionError("Not connected")

        self._client.delete_folder(folder)

    def rename_folder(self, old_name: str, new_name: str) -> None:
        """Rename a folder."""
        if not self._client:
            raise ConnectionError("Not connected")

        self._client.rename_folder(old_name, new_name)

    def idle_start(self) -> None:
        """Start IDLE mode for push notifications."""
        if not self._client:
            raise ConnectionError("Not connected")

        self._client.idle()

    def idle_check(self, timeout: float = 30.0) -> list:
        """Check for IDLE notifications."""
        if not self._client:
            raise ConnectionError("Not connected")

        return self._client.idle_check(timeout=timeout)

    def idle_done(self) -> None:
        """End IDLE mode."""
        if not self._client:
            raise ConnectionError("Not connected")

        self._client.idle_done()
