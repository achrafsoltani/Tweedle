# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-02

### Added
- Initial release of Tweedle email client
- Multi-account email support with IMAP/SMTP
- Secure credential storage using system keyring
- HTML email rendering with QWebEngineView
- Three-pane UI layout (folders, message list, preview)
- Compose window with reply, reply-all, and forward
- Attachment support (view and send)
- Message search functionality
- Provider presets for Gmail, Outlook, Yahoo, iCloud
- HTML sanitization for security
- Keyboard shortcuts for common actions
- Linux desktop integration
- Cross-platform builds for Linux and Windows

### Security
- Passwords stored in system keyring (not in config files)
- HTML content sanitized to prevent XSS
- External links open in system browser
- TLS/SSL encrypted connections

## [Unreleased]

### Planned
- Message caching for offline access
- Contact autocomplete
- Signature management
- Message rules and filters
- Dark theme support
- Notification system
- Calendar integration
