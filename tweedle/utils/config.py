"""Configuration management for Tweedle"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


def get_config_dir() -> Path:
    """Get the configuration directory for Tweedle."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        config_dir = Path(xdg_config) / "tweedle"
    else:
        config_dir = Path.home() / ".config" / "tweedle"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    """Get the data directory for Tweedle."""
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        data_dir = Path(xdg_data) / "tweedle"
    else:
        data_dir = Path.home() / ".local" / "share" / "tweedle"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@dataclass
class AccountConfig:
    """Configuration for a single email account (non-sensitive data only)."""
    id: str
    name: str
    email: str
    imap_server: str
    imap_port: int = 993
    imap_ssl: bool = True
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_ssl: bool = False
    smtp_starttls: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AccountConfig":
        return cls(**data)


@dataclass
class AppConfig:
    """Application configuration."""
    accounts: list[AccountConfig] = field(default_factory=list)
    default_account_id: Optional[str] = None
    window_width: int = 1200
    window_height: int = 800
    sidebar_width: int = 200
    message_list_height: int = 300
    check_interval_minutes: int = 5

    def to_dict(self) -> dict:
        data = asdict(self)
        data["accounts"] = [acc.to_dict() for acc in self.accounts]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        accounts_data = data.pop("accounts", [])
        accounts = [AccountConfig.from_dict(acc) for acc in accounts_data]
        return cls(accounts=accounts, **data)


class ConfigManager:
    """Manages application configuration."""

    def __init__(self):
        self.config_file = get_config_dir() / "config.json"
        self._config: Optional[AppConfig] = None

    @property
    def config(self) -> AppConfig:
        if self._config is None:
            self._config = self.load()
        return self._config

    def load(self) -> AppConfig:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                return AppConfig.from_dict(data)
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
        return AppConfig()

    def save(self) -> None:
        """Save configuration to file."""
        with open(self.config_file, "w") as f:
            json.dump(self.config.to_dict(), f, indent=2)

    def add_account(self, account: AccountConfig) -> None:
        """Add a new account."""
        self.config.accounts.append(account)
        if self.config.default_account_id is None:
            self.config.default_account_id = account.id
        self.save()

    def remove_account(self, account_id: str) -> None:
        """Remove an account by ID."""
        self.config.accounts = [
            acc for acc in self.config.accounts if acc.id != account_id
        ]
        if self.config.default_account_id == account_id:
            if self.config.accounts:
                self.config.default_account_id = self.config.accounts[0].id
            else:
                self.config.default_account_id = None
        self.save()

    def get_account(self, account_id: str) -> Optional[AccountConfig]:
        """Get an account by ID."""
        for acc in self.config.accounts:
            if acc.id == account_id:
                return acc
        return None

    def update_account(self, account: AccountConfig) -> None:
        """Update an existing account."""
        for i, acc in enumerate(self.config.accounts):
            if acc.id == account.id:
                self.config.accounts[i] = account
                break
        self.save()


config_manager = ConfigManager()
