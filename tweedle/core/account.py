"""Account model with secure credential management."""

import uuid
import keyring
from dataclasses import dataclass
from typing import Optional

from tweedle.utils.config import AccountConfig, config_manager

KEYRING_SERVICE = "tweedle"


@dataclass
class Account:
    """Email account with credentials."""
    config: AccountConfig
    _password: Optional[str] = None

    @property
    def id(self) -> str:
        return self.config.id

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def email(self) -> str:
        return self.config.email

    @property
    def password(self) -> Optional[str]:
        """Get password from keyring or cache."""
        if self._password is None:
            self._password = keyring.get_password(KEYRING_SERVICE, self.config.id)
        return self._password

    def set_password(self, password: str) -> None:
        """Store password in system keyring."""
        keyring.set_password(KEYRING_SERVICE, self.config.id, password)
        self._password = password

    def delete_password(self) -> None:
        """Delete password from keyring."""
        try:
            keyring.delete_password(KEYRING_SERVICE, self.config.id)
        except keyring.errors.PasswordDeleteError:
            pass
        self._password = None


class AccountManager:
    """Manages email accounts."""

    def __init__(self):
        self._accounts: dict[str, Account] = {}

    def load_accounts(self) -> list[Account]:
        """Load all accounts from config."""
        self._accounts.clear()
        for acc_config in config_manager.config.accounts:
            account = Account(config=acc_config)
            self._accounts[account.id] = account
        return list(self._accounts.values())

    def get_account(self, account_id: str) -> Optional[Account]:
        """Get an account by ID."""
        return self._accounts.get(account_id)

    def get_default_account(self) -> Optional[Account]:
        """Get the default account."""
        default_id = config_manager.config.default_account_id
        if default_id:
            return self._accounts.get(default_id)
        if self._accounts:
            return next(iter(self._accounts.values()))
        return None

    def create_account(
        self,
        name: str,
        email: str,
        password: str,
        imap_server: str,
        imap_port: int = 993,
        imap_ssl: bool = True,
        smtp_server: str = "",
        smtp_port: int = 587,
        smtp_ssl: bool = False,
        smtp_starttls: bool = True,
    ) -> Account:
        """Create and save a new account."""
        account_id = str(uuid.uuid4())

        acc_config = AccountConfig(
            id=account_id,
            name=name,
            email=email,
            imap_server=imap_server,
            imap_port=imap_port,
            imap_ssl=imap_ssl,
            smtp_server=smtp_server or imap_server.replace("imap", "smtp"),
            smtp_port=smtp_port,
            smtp_ssl=smtp_ssl,
            smtp_starttls=smtp_starttls,
        )

        config_manager.add_account(acc_config)

        account = Account(config=acc_config)
        account.set_password(password)

        self._accounts[account.id] = account
        return account

    def update_account(
        self,
        account_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        imap_server: Optional[str] = None,
        imap_port: Optional[int] = None,
        imap_ssl: Optional[bool] = None,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_ssl: Optional[bool] = None,
        smtp_starttls: Optional[bool] = None,
    ) -> Optional[Account]:
        """Update an existing account."""
        account = self._accounts.get(account_id)
        if not account:
            return None

        config = account.config
        if name is not None:
            config.name = name
        if email is not None:
            config.email = email
        if imap_server is not None:
            config.imap_server = imap_server
        if imap_port is not None:
            config.imap_port = imap_port
        if imap_ssl is not None:
            config.imap_ssl = imap_ssl
        if smtp_server is not None:
            config.smtp_server = smtp_server
        if smtp_port is not None:
            config.smtp_port = smtp_port
        if smtp_ssl is not None:
            config.smtp_ssl = smtp_ssl
        if smtp_starttls is not None:
            config.smtp_starttls = smtp_starttls

        config_manager.update_account(config)

        if password is not None:
            account.set_password(password)

        return account

    def delete_account(self, account_id: str) -> bool:
        """Delete an account and its credentials."""
        account = self._accounts.get(account_id)
        if not account:
            return False

        account.delete_password()
        config_manager.remove_account(account_id)
        del self._accounts[account_id]
        return True

    @property
    def accounts(self) -> list[Account]:
        """Get all accounts."""
        return list(self._accounts.values())


account_manager = AccountManager()
