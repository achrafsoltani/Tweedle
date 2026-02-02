# Tweedle - Technical Documentation

## Architecture Overview

Tweedle follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    UI Layer (PySide6)                    │
│  ┌─────────┐ ┌─────────────┐ ┌────────────┐ ┌─────────┐ │
│  │ Main    │ │ Message     │ │ Compose    │ │ Account │ │
│  │ Window  │ │ View        │ │ Window     │ │ Dialog  │ │
│  └────┬────┘ └──────┬──────┘ └─────┬──────┘ └────┬────┘ │
└───────┼─────────────┼──────────────┼─────────────┼──────┘
        │             │              │             │
┌───────┼─────────────┼──────────────┼─────────────┼──────┐
│       ▼             ▼              ▼             ▼      │
│              Qt Models Layer                            │
│  ┌─────────────────┐  ┌─────────────────────┐          │
│  │  FolderModel    │  │   MessageModel      │          │
│  │ (QStandardItem) │  │ (QAbstractTable)    │          │
│  └────────┬────────┘  └──────────┬──────────┘          │
└───────────┼──────────────────────┼─────────────────────┘
            │                      │
┌───────────┼──────────────────────┼─────────────────────┐
│           ▼                      ▼                     │
│                 Core Layer                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │ IMAPClient  │ │ SMTPClient  │ │ AccountManager  │   │
│  └──────┬──────┘ └──────┬──────┘ └────────┬────────┘   │
│         │               │                  │           │
│         ▼               ▼                  ▼           │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Workers (QThread)                  │   │
│  │  ConnectWorker, FetchWorker, SendWorker, etc.  │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
            │                      │
┌───────────┼──────────────────────┼─────────────────────┐
│           ▼                      ▼                     │
│                 Utils Layer                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │   Config    │ │ HTMLSaniti- │ │    Message      │   │
│  │  Manager    │ │    zer      │ │    Parser       │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└────────────────────────────────────────────────────────┘
```

## Module Descriptions

### Core Module (`tweedle/core/`)

#### `account.py`
Manages email accounts and credentials.

- `Account`: Dataclass representing an email account
- `AccountManager`: Singleton managing all accounts
- Uses `keyring` for secure password storage

```python
# Example usage
account = account_manager.create_account(
    name="Personal",
    email="user@gmail.com",
    password="app-password",
    imap_server="imap.gmail.com",
    smtp_server="smtp.gmail.com"
)
```

#### `imap_client.py`
IMAP protocol implementation using `imapclient`.

Key methods:
- `connect()` / `disconnect()` - Session management
- `list_folders()` - Get mailbox structure
- `fetch_message_headers()` - Efficient header fetching
- `fetch_message()` - Full message retrieval
- `search()` - Server-side search
- `mark_read()` / `mark_flagged()` - Flag operations
- `move_messages()` / `delete_messages()` - Message management

#### `smtp_client.py`
SMTP protocol implementation using Python's `smtplib`.

Key methods:
- `send_message()` - Send with optional HTML and attachments
- `send_reply()` - Reply with proper threading headers
- `send_forward()` - Forward with attachments

#### `message.py`
Email message parsing and models.

Classes:
- `EmailAddress`: Parsed email address (name + address)
- `Attachment`: File attachment data
- `Message`: Full email message
- `MessageHeader`: Lightweight header for list display

Functions:
- `parse_message()` - Parse raw email bytes
- `parse_message_header()` - Parse IMAP envelope

#### `workers.py`
Background workers using QThread for async operations.

Workers:
- `ConnectWorker` - Async IMAP connection
- `FetchFoldersWorker` - Async folder listing
- `FetchMessagesWorker` - Async message header fetch
- `FetchMessageWorker` - Async full message fetch
- `SearchWorker` - Async search
- `SendMessageWorker` - Async SMTP send
- `ModifyFlagsWorker` - Async flag changes
- `MoveMessagesWorker` - Async move
- `DeleteMessagesWorker` - Async delete

### Models Module (`tweedle/models/`)

#### `folder_model.py`
Qt model for folder tree view.

- `FolderItem`: Custom QStandardItem with folder metadata
- `FolderModel`: QStandardItemModel for tree structure
- Handles folder hierarchy and special folder detection

#### `message_model.py`
Qt model for message list view.

- `MessageModel`: QAbstractTableModel for tabular display
- Columns: From, Subject, Date
- Handles read/unread styling and flag icons

### UI Module (`tweedle/ui/`)

#### `main_window.py`
Main application window.

Components:
- Menu bar with File, Edit, View, Message menus
- Toolbar with account selector and action buttons
- Three-pane splitter layout
- Status bar with connection status

#### `folder_tree.py`
Folder navigation widget.

- QTreeView with custom folder model
- Emits `folder_selected` signal
- Auto-expands folder hierarchy

#### `message_list.py`
Message list view.

- QTableView with custom message model
- Multi-selection support
- Context menu for actions
- Emits `message_selected` and `messages_deleted` signals

#### `message_view.py`
HTML email viewer.

- QWebEngineView for HTML rendering
- Header widget showing From, To, Date, Subject
- Attachment bar for downloading
- External links open in browser

#### `compose_window.py`
Email composition window.

Features:
- To, Cc, Bcc, Subject fields
- Plain text body editor
- Attachment selector
- Reply/Forward setup with quoting
- Send confirmation and draft protection

#### `account_dialog.py`
Account configuration dialog.

- Basic tab: Name, email, password
- Server tab: IMAP/SMTP settings
- Provider presets for quick setup

#### `search_bar.py`
Search widget.

- Search input with clear button
- Enter to search, Escape to clear
- Ctrl+K shortcut to focus

#### `attachment_widget.py`
Attachment handling.

- `AttachmentBar`: Display attachments in message view
- `AttachmentSelector`: Add attachments in compose

### Utils Module (`tweedle/utils/`)

#### `config.py`
Configuration management.

- `AppConfig`: Application settings
- `AccountConfig`: Account settings (non-sensitive)
- `ConfigManager`: Load/save JSON config

Config location:
- Linux: `~/.config/tweedle/config.json`
- Windows: `%APPDATA%/tweedle/config.json`

#### `html_sanitizer.py`
HTML sanitization for safe display.

- Removes script tags and event handlers
- Sanitizes CSS (removes expressions, behaviors)
- Blocks dangerous URL protocols
- Allows safe structural HTML

## Data Flow

### Fetching Messages

```
User clicks folder
       │
       ▼
MainWindow._on_folder_selected(folder)
       │
       ▼
FetchMessagesWorker.start()
       │
       ▼ (in background)
IMAPClient.fetch_message_headers()
       │
       ▼
Worker.signals.result.emit(headers)
       │
       ▼
MainWindow._on_messages_fetched()
       │
       ▼
MessageModel.set_messages(headers)
       │
       ▼
UI updates automatically
```

### Sending Messages

```
User clicks Send
       │
       ▼
ComposeWindow._on_send()
       │
       ▼
SendMessageWorker.start()
       │
       ▼ (in background)
SMTPClient.send_message()
       │
       ▼
Worker.signals.result.emit()
       │
       ▼
ComposeWindow closes
MainWindow shows "Message sent"
```

## Configuration File Format

```json
{
  "accounts": [
    {
      "id": "uuid-string",
      "name": "Personal Gmail",
      "email": "user@gmail.com",
      "imap_server": "imap.gmail.com",
      "imap_port": 993,
      "imap_ssl": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "smtp_ssl": false,
      "smtp_starttls": true
    }
  ],
  "default_account_id": "uuid-string",
  "window_width": 1200,
  "window_height": 800,
  "sidebar_width": 200,
  "message_list_height": 300,
  "check_interval_minutes": 5
}
```

## Security Considerations

### Credential Storage
- Passwords never stored in config files
- Uses system keyring via `keyring` library:
  - Linux: GNOME Keyring or KWallet
  - Windows: Windows Credential Manager
  - macOS: Keychain

### HTML Safety
- All HTML sanitized before display
- Scripts removed completely
- Event handlers stripped
- Dangerous CSS removed
- External links open in browser

### Network Security
- SSL/TLS for IMAP connections
- STARTTLS or SSL for SMTP
- Certificate validation enabled

## Building and Packaging

### PyInstaller Configuration

The build creates a one-directory bundle with:
- Main executable
- Python runtime
- All dependencies
- Qt plugins and resources

Hidden imports required:
- PySide6 modules
- imapclient
- keyring backends

### Platform-Specific Notes

**Linux**:
- Requires `libsecret` for keyring
- Desktop file for application menu
- Icon in XDG icon directories

**Windows**:
- Uses Windows Credential Manager
- ICO file generated from PNG
- No installer, portable ZIP

## Testing

### Test Structure

```
tests/
├── __init__.py
├── test_config.py      # Config loading/saving
├── test_message.py     # Message parsing
├── test_sanitizer.py   # HTML sanitization
└── test_models.py      # Qt model tests
```

### Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_message.py -v

# With coverage
python -m pytest tests/ --cov=tweedle
```

## Future Enhancements

### Planned Features
- Message caching with SQLite
- Contact management and autocomplete
- Email signatures
- Message rules/filters
- Dark theme
- System tray with notifications
- Calendar/event support
- PGP/GPG encryption

### Performance Improvements
- Lazy loading for large folders
- Background sync
- Message threading view
- Full-text search indexing
