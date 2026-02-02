---
layout: default
title: Tweedle - Modern Email Client
---

# Tweedle

A modern, full-featured email client for Linux and Windows built with Python and Qt6.

## Features

- **Multi-account support** - Manage multiple email accounts from different providers
- **IMAP/SMTP support** - Full protocol support for receiving and sending emails
- **HTML email rendering** - View HTML emails with embedded images
- **Secure credential storage** - Passwords stored in system keyring
- **Attachment support** - View and send email attachments
- **Search functionality** - Search messages by subject, sender, or content

## Quick Start

### Download

Get the latest release for your platform:

- **Linux**: Download the `.deb` package or portable `.tar.gz`
- **Windows**: Download the portable `.zip` archive

[View Releases](https://github.com/achrafsoltani/tweedle/releases)

### Installation

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

Extract the ZIP file and run `Tweedle.exe`.

## Supported Providers

Quick setup presets are available for:

- Gmail (requires App Password)
- Outlook / Hotmail
- Yahoo Mail
- iCloud Mail
- Any IMAP/SMTP server

## Screenshots

*Coming soon*

## Requirements

- Python 3.11+ (for running from source)
- PySide6 (Qt6 for Python)
- System keyring (GNOME Keyring, KWallet, or Windows Credential Manager)

## License

This project is licensed under the GNU General Public License v2.0.

## Author

[Achraf SOLTANI](https://github.com/achrafsoltani)

---

[View on GitHub](https://github.com/achrafsoltani/tweedle) | [Report an Issue](https://github.com/achrafsoltani/tweedle/issues)
