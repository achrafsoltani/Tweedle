"""Account configuration dialog."""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QDialogButtonBox,
    QLabel,
    QGroupBox,
    QMessageBox,
    QTabWidget,
    QWidget,
)
from PySide6.QtCore import Qt

from tweedle.core.account import Account, account_manager


PROVIDER_PRESETS = {
    "Gmail": {
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_ssl": False,
        "smtp_starttls": True,
    },
    "Outlook/Hotmail": {
        "imap_server": "outlook.office365.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_server": "smtp.office365.com",
        "smtp_port": 587,
        "smtp_ssl": False,
        "smtp_starttls": True,
    },
    "Yahoo": {
        "imap_server": "imap.mail.yahoo.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_server": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "smtp_ssl": False,
        "smtp_starttls": True,
    },
    "iCloud": {
        "imap_server": "imap.mail.me.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_server": "smtp.mail.me.com",
        "smtp_port": 587,
        "smtp_ssl": False,
        "smtp_starttls": True,
    },
}


class AccountDialog(QDialog):
    """Dialog for adding or editing an email account."""

    def __init__(self, parent=None, account: Optional[Account] = None):
        super().__init__(parent)
        self._account = account
        self._created_account: Optional[Account] = None

        self.setWindowTitle("Edit Account" if account else "Add Account")
        self.setMinimumWidth(450)

        self._setup_ui()

        if account:
            self._load_account(account)

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)

        basic_form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("My Email Account")
        basic_form.addRow("Account Name:", self.name_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("user@example.com")
        basic_form.addRow("Email Address:", self.email_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("App password or regular password")
        basic_form.addRow("Password:", self.password_edit)

        basic_layout.addLayout(basic_form)

        preset_group = QGroupBox("Quick Setup")
        preset_layout = QHBoxLayout(preset_group)

        for name in PROVIDER_PRESETS:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, n=name: self._apply_preset(n))
            preset_layout.addWidget(btn)

        preset_layout.addStretch()
        basic_layout.addWidget(preset_group)

        basic_layout.addStretch()
        tabs.addTab(basic_tab, "Account")

        server_tab = QWidget()
        server_layout = QVBoxLayout(server_tab)

        imap_group = QGroupBox("IMAP (Incoming)")
        imap_form = QFormLayout(imap_group)

        self.imap_server_edit = QLineEdit()
        self.imap_server_edit.setPlaceholderText("imap.example.com")
        imap_form.addRow("Server:", self.imap_server_edit)

        self.imap_port_spin = QSpinBox()
        self.imap_port_spin.setRange(1, 65535)
        self.imap_port_spin.setValue(993)
        imap_form.addRow("Port:", self.imap_port_spin)

        self.imap_ssl_check = QCheckBox("Use SSL/TLS")
        self.imap_ssl_check.setChecked(True)
        imap_form.addRow("", self.imap_ssl_check)

        server_layout.addWidget(imap_group)

        smtp_group = QGroupBox("SMTP (Outgoing)")
        smtp_form = QFormLayout(smtp_group)

        self.smtp_server_edit = QLineEdit()
        self.smtp_server_edit.setPlaceholderText("smtp.example.com")
        smtp_form.addRow("Server:", self.smtp_server_edit)

        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        self.smtp_port_spin.setValue(587)
        smtp_form.addRow("Port:", self.smtp_port_spin)

        self.smtp_ssl_check = QCheckBox("Use SSL/TLS")
        self.smtp_ssl_check.setChecked(False)
        smtp_form.addRow("", self.smtp_ssl_check)

        self.smtp_starttls_check = QCheckBox("Use STARTTLS")
        self.smtp_starttls_check.setChecked(True)
        smtp_form.addRow("", self.smtp_starttls_check)

        server_layout.addWidget(smtp_group)
        server_layout.addStretch()

        tabs.addTab(server_tab, "Server Settings")

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _apply_preset(self, provider: str):
        """Apply a provider preset."""
        preset = PROVIDER_PRESETS.get(provider)
        if not preset:
            return

        self.imap_server_edit.setText(preset["imap_server"])
        self.imap_port_spin.setValue(preset["imap_port"])
        self.imap_ssl_check.setChecked(preset["imap_ssl"])
        self.smtp_server_edit.setText(preset["smtp_server"])
        self.smtp_port_spin.setValue(preset["smtp_port"])
        self.smtp_ssl_check.setChecked(preset["smtp_ssl"])
        self.smtp_starttls_check.setChecked(preset["smtp_starttls"])

    def _load_account(self, account: Account):
        """Load existing account data into the form."""
        config = account.config

        self.name_edit.setText(config.name)
        self.email_edit.setText(config.email)

        self.imap_server_edit.setText(config.imap_server)
        self.imap_port_spin.setValue(config.imap_port)
        self.imap_ssl_check.setChecked(config.imap_ssl)

        self.smtp_server_edit.setText(config.smtp_server)
        self.smtp_port_spin.setValue(config.smtp_port)
        self.smtp_ssl_check.setChecked(config.smtp_ssl)
        self.smtp_starttls_check.setChecked(config.smtp_starttls)

    def _validate(self) -> bool:
        """Validate the form data."""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter an account name.")
            return False

        if not self.email_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter an email address.")
            return False

        if not self._account and not self.password_edit.text():
            QMessageBox.warning(self, "Validation Error", "Please enter a password.")
            return False

        if not self.imap_server_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter an IMAP server.")
            return False

        if not self.smtp_server_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter an SMTP server.")
            return False

        return True

    def _on_accept(self):
        """Handle dialog acceptance."""
        if not self._validate():
            return

        name = self.name_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.password_edit.text() if self.password_edit.text() else None

        imap_server = self.imap_server_edit.text().strip()
        imap_port = self.imap_port_spin.value()
        imap_ssl = self.imap_ssl_check.isChecked()

        smtp_server = self.smtp_server_edit.text().strip()
        smtp_port = self.smtp_port_spin.value()
        smtp_ssl = self.smtp_ssl_check.isChecked()
        smtp_starttls = self.smtp_starttls_check.isChecked()

        try:
            if self._account:
                account_manager.update_account(
                    self._account.id,
                    name=name,
                    email=email,
                    password=password,
                    imap_server=imap_server,
                    imap_port=imap_port,
                    imap_ssl=imap_ssl,
                    smtp_server=smtp_server,
                    smtp_port=smtp_port,
                    smtp_ssl=smtp_ssl,
                    smtp_starttls=smtp_starttls,
                )
                self._created_account = self._account
            else:
                self._created_account = account_manager.create_account(
                    name=name,
                    email=email,
                    password=password,
                    imap_server=imap_server,
                    imap_port=imap_port,
                    imap_ssl=imap_ssl,
                    smtp_server=smtp_server,
                    smtp_port=smtp_port,
                    smtp_ssl=smtp_ssl,
                    smtp_starttls=smtp_starttls,
                )

            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save account:\n{e}",
            )

    def get_account(self) -> Optional[Account]:
        """Get the created/updated account."""
        return self._created_account
