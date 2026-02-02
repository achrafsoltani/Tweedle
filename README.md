# Tweedle

A modern, full-featured email client for Linux and Windows built with Python and Qt6.

![License](https://img.shields.io/badge/license-GPL--2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.6+-green.svg)

## Features

### Email Management
- **Multi-account support** - Manage multiple email accounts from different providers
- **IMAP support** - Full IMAP protocol support for receiving emails
- **SMTP support** - Send emails with attachments
- **HTML email rendering** - View HTML emails with embedded images
- **Secure credential storage** - Passwords stored in system keyring (GNOME Keyring, KWallet, Windows Credential Manager)

### User Interface
- **Three-pane layout** - Folder tree, message list, and message preview
- **Search functionality** - Search messages by subject, sender, or content
- **Keyboard shortcuts** - Efficient navigation and actions
- **Modern Qt6 design** - Clean, responsive interface

### Compose & Reply
- **Rich compose window** - Write new emails with attachments
- **Reply and Reply All** - Respond to emails with proper quoting
- **Forward** - Forward emails with attachments
- **Draft support** - Unsent messages are protected from accidental close

### Supported Providers
Quick setup presets for popular email providers:
- Gmail (requires App Password)
- Outlook / Hotmail
- Yahoo Mail
- iCloud Mail
- Any IMAP/SMTP server

## Installation

### From Release (Recommended)

Download the latest release for your platform:
- **Linux**: `.deb` package or portable `.tar.gz`
- **Windows**: Portable `.zip` archive

#### Linux (Debian/Ubuntu)
```bash
sudo dpkg -i tweedle_1.0.0_amd64.deb
```

#### Linux (Portable)
```bash
tar -xzvf Tweedle-1.0.0-linux-x64.tar.gz
cd Tweedle
./Tweedle
```

#### Windows
Extract the ZIP and run `Tweedle.exe`

### From Source

```bash
# Clone the repository
git clone https://github.com/achrafsoltani/tweedle.git
cd tweedle

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Configuration

### Gmail Setup
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Create a new app password for "Mail"
3. Use your Gmail address and the App Password in Tweedle

### Outlook Setup
Use your regular email and password. If 2FA is enabled, generate an App Password.

### Generic IMAP/SMTP
For other providers, you'll need:
- IMAP server address and port (usually 993 with SSL)
- SMTP server address and port (usually 587 with STARTTLS)
- Your email address and password

## Keyboard Shortcuts

### Navigation
| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Focus search bar |
| `Escape` | Clear search |
| `F5` | Refresh current folder |

### Messages
| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New message |
| `Ctrl+R` | Reply |
| `Ctrl+Shift+R` | Reply All |
| `Ctrl+F` | Forward |
| `Delete` | Delete selected messages |
| `R` | Mark as read |
| `U` | Mark as unread |

### Compose Window
| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Send message |
| `Escape` | Close (with confirmation) |

### Application
| Shortcut | Action |
|----------|--------|
| `Ctrl+Q` | Quit |

## Project Structure

```
tweedle/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── build.py                   # Build script
├── tweedle.desktop           # Linux desktop entry
├── tweedle/
│   ├── app.py                # Application initialization
│   ├── core/                 # Business logic
│   │   ├── account.py        # Account & credential management
│   │   ├── imap_client.py    # IMAP operations
│   │   ├── smtp_client.py    # SMTP operations
│   │   ├── message.py        # Message parsing
│   │   └── workers.py        # Background threads
│   ├── models/               # Qt data models
│   │   ├── folder_model.py   # Folder tree model
│   │   └── message_model.py  # Message list model
│   ├── ui/                   # UI components
│   │   ├── main_window.py    # Main window
│   │   ├── folder_tree.py    # Folder navigation
│   │   ├── message_list.py   # Message list
│   │   ├── message_view.py   # HTML viewer
│   │   ├── compose_window.py # Compose dialog
│   │   ├── account_dialog.py # Account setup
│   │   ├── search_bar.py     # Search widget
│   │   └── attachment_widget.py
│   └── utils/                # Utilities
│       ├── config.py         # Configuration
│       └── html_sanitizer.py # HTML sanitization
├── resources/
│   ├── icons/                # Application icons
│   └── screenshots/          # Documentation images
├── tests/                    # Test suite
└── docs/                     # Documentation
```

## Building from Source

### Prerequisites
- Python 3.11+
- pip

### Build Commands

```bash
# Clean build artifacts
python build.py clean

# Build standalone executable
python build.py build

# Run tests
python build.py test

# Create Windows ICO (Windows only)
python build.py ico
```

### Dependencies
- `PySide6` - Qt6 for Python (GUI)
- `PySide6-WebEngine` - Web engine for HTML rendering
- `imapclient` - IMAP protocol support
- `keyring` - Secure credential storage

## Security

- **No plaintext passwords** - Credentials stored in system keyring
- **HTML sanitization** - Prevents XSS attacks in email content
- **TLS/SSL** - Encrypted connections to mail servers
- **External links** - Opened in default browser, not in-app

## Development

### Running Tests
```bash
pip install pytest
python -m pytest tests/ -v
```

### Code Style
The project follows PEP 8 guidelines. Type hints are used throughout.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [PySide6](https://wiki.qt.io/Qt_for_Python) - Qt for Python
- [IMAPClient](https://imapclient.readthedocs.io/) - IMAP library
- [keyring](https://keyring.readthedocs.io/) - Secure credential storage

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Author

**Achraf SOLTANI** - [GitHub](https://github.com/achrafsoltani)
