"""Background workers for async operations."""

from typing import Optional, Callable, Any
from PySide6.QtCore import QThread, Signal, QObject

from tweedle.core.account import Account
from tweedle.core.imap_client import IMAPClientWrapper
from tweedle.core.smtp_client import SMTPClientWrapper
from tweedle.core.message import Message, MessageHeader


class WorkerSignals(QObject):
    """Signals for worker threads."""
    finished = Signal()
    error = Signal(str)
    result = Signal(object)
    progress = Signal(int, int)


class BaseWorker(QThread):
    """Base worker thread class."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = WorkerSignals()
        self._cancelled = False

    def cancel(self):
        """Cancel the worker."""
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled


class ConnectWorker(BaseWorker):
    """Worker for connecting to IMAP server."""

    def __init__(self, account: Account, parent=None):
        super().__init__(parent)
        self.account = account
        self.client: Optional[IMAPClientWrapper] = None

    def run(self):
        try:
            self.client = IMAPClientWrapper(self.account)
            self.client.connect()
            self.signals.result.emit(self.client)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class FetchFoldersWorker(BaseWorker):
    """Worker for fetching folder list."""

    def __init__(self, client: IMAPClientWrapper, parent=None):
        super().__init__(parent)
        self.client = client

    def run(self):
        try:
            folders = self.client.list_folders()
            folder_info = []
            for name, delimiter in folders:
                try:
                    total, unread = self.client.get_message_count(name)
                    folder_info.append((name, delimiter, total, unread))
                except Exception:
                    folder_info.append((name, delimiter, 0, 0))
            self.signals.result.emit(folder_info)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class FetchMessagesWorker(BaseWorker):
    """Worker for fetching message headers."""

    def __init__(
        self,
        client: IMAPClientWrapper,
        folder: str,
        limit: int = 50,
        offset: int = 0,
        parent=None,
    ):
        super().__init__(parent)
        self.client = client
        self.folder = folder
        self.limit = limit
        self.offset = offset

    def run(self):
        try:
            headers = self.client.fetch_message_headers(
                self.folder,
                limit=self.limit,
                offset=self.offset,
            )
            self.signals.result.emit(headers)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class FetchMessageWorker(BaseWorker):
    """Worker for fetching a complete message."""

    def __init__(
        self,
        client: IMAPClientWrapper,
        folder: str,
        uid: int,
        parent=None,
    ):
        super().__init__(parent)
        self.client = client
        self.folder = folder
        self.uid = uid

    def run(self):
        try:
            message = self.client.fetch_message(self.folder, self.uid)
            self.signals.result.emit(message)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class SearchWorker(BaseWorker):
    """Worker for searching messages."""

    def __init__(
        self,
        client: IMAPClientWrapper,
        folder: str,
        query: str,
        limit: int = 50,
        parent=None,
    ):
        super().__init__(parent)
        self.client = client
        self.folder = folder
        self.query = query
        self.limit = limit

    def run(self):
        try:
            headers = self.client.search(
                self.folder,
                self.query,
                limit=self.limit,
            )
            self.signals.result.emit(headers)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class SendMessageWorker(BaseWorker):
    """Worker for sending a message."""

    def __init__(
        self,
        account: Account,
        to: list[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        reply_to: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None,
        attachments: Optional[list[tuple[str, bytes, str]]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.account = account
        self.to = to
        self.subject = subject
        self.body = body
        self.html_body = html_body
        self.cc = cc
        self.bcc = bcc
        self.reply_to = reply_to
        self.in_reply_to = in_reply_to
        self.references = references
        self.attachments = attachments

    def run(self):
        try:
            smtp = SMTPClientWrapper(self.account)
            smtp.send_message(
                to=self.to,
                subject=self.subject,
                body=self.body,
                html_body=self.html_body,
                cc=self.cc,
                bcc=self.bcc,
                reply_to=self.reply_to,
                in_reply_to=self.in_reply_to,
                references=self.references,
                attachments=self.attachments,
            )
            self.signals.result.emit(True)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class ModifyFlagsWorker(BaseWorker):
    """Worker for modifying message flags."""

    def __init__(
        self,
        client: IMAPClientWrapper,
        folder: str,
        uids: list[int],
        operation: str,
        parent=None,
    ):
        super().__init__(parent)
        self.client = client
        self.folder = folder
        self.uids = uids
        self.operation = operation

    def run(self):
        try:
            if self.operation == "mark_read":
                self.client.mark_read(self.folder, self.uids)
            elif self.operation == "mark_unread":
                self.client.mark_unread(self.folder, self.uids)
            elif self.operation == "mark_flagged":
                self.client.mark_flagged(self.folder, self.uids)
            elif self.operation == "mark_unflagged":
                self.client.mark_unflagged(self.folder, self.uids)
            self.signals.result.emit(True)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class MoveMessagesWorker(BaseWorker):
    """Worker for moving messages."""

    def __init__(
        self,
        client: IMAPClientWrapper,
        folder: str,
        uids: list[int],
        dest_folder: str,
        parent=None,
    ):
        super().__init__(parent)
        self.client = client
        self.folder = folder
        self.uids = uids
        self.dest_folder = dest_folder

    def run(self):
        try:
            self.client.move_messages(self.folder, self.uids, self.dest_folder)
            self.signals.result.emit(True)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class DeleteMessagesWorker(BaseWorker):
    """Worker for deleting messages."""

    def __init__(
        self,
        client: IMAPClientWrapper,
        folder: str,
        uids: list[int],
        parent=None,
    ):
        super().__init__(parent)
        self.client = client
        self.folder = folder
        self.uids = uids

    def run(self):
        try:
            self.client.delete_messages(self.folder, self.uids)
            self.signals.result.emit(True)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()
