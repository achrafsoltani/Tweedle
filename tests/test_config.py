"""Tests for configuration management."""

import json
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tweedle.utils.config import AccountConfig, AppConfig, ConfigManager


class TestAccountConfig:
    """Tests for AccountConfig dataclass."""

    def test_create_account_config(self):
        """Test creating an AccountConfig."""
        config = AccountConfig(
            id="test-id",
            name="Test Account",
            email="test@example.com",
            imap_server="imap.example.com",
        )

        assert config.id == "test-id"
        assert config.name == "Test Account"
        assert config.email == "test@example.com"
        assert config.imap_server == "imap.example.com"
        assert config.imap_port == 993
        assert config.imap_ssl is True
        assert config.smtp_port == 587
        assert config.smtp_starttls is True

    def test_account_config_to_dict(self):
        """Test serializing AccountConfig to dict."""
        config = AccountConfig(
            id="test-id",
            name="Test Account",
            email="test@example.com",
            imap_server="imap.example.com",
            smtp_server="smtp.example.com",
        )

        data = config.to_dict()

        assert data["id"] == "test-id"
        assert data["name"] == "Test Account"
        assert data["email"] == "test@example.com"
        assert data["imap_server"] == "imap.example.com"
        assert data["smtp_server"] == "smtp.example.com"

    def test_account_config_from_dict(self):
        """Test deserializing AccountConfig from dict."""
        data = {
            "id": "test-id",
            "name": "Test Account",
            "email": "test@example.com",
            "imap_server": "imap.example.com",
            "imap_port": 993,
            "imap_ssl": True,
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "smtp_ssl": False,
            "smtp_starttls": True,
        }

        config = AccountConfig.from_dict(data)

        assert config.id == "test-id"
        assert config.name == "Test Account"
        assert config.email == "test@example.com"
        assert config.imap_server == "imap.example.com"


class TestAppConfig:
    """Tests for AppConfig dataclass."""

    def test_create_empty_app_config(self):
        """Test creating empty AppConfig."""
        config = AppConfig()

        assert config.accounts == []
        assert config.default_account_id is None
        assert config.window_width == 1200
        assert config.window_height == 800

    def test_app_config_with_accounts(self):
        """Test AppConfig with accounts."""
        account = AccountConfig(
            id="acc-1",
            name="Account 1",
            email="test@example.com",
            imap_server="imap.example.com",
        )

        config = AppConfig(
            accounts=[account],
            default_account_id="acc-1",
        )

        assert len(config.accounts) == 1
        assert config.accounts[0].id == "acc-1"
        assert config.default_account_id == "acc-1"

    def test_app_config_roundtrip(self):
        """Test serializing and deserializing AppConfig."""
        account = AccountConfig(
            id="acc-1",
            name="Account 1",
            email="test@example.com",
            imap_server="imap.example.com",
            smtp_server="smtp.example.com",
        )

        original = AppConfig(
            accounts=[account],
            default_account_id="acc-1",
            window_width=1400,
            window_height=900,
        )

        data = original.to_dict()
        restored = AppConfig.from_dict(data)

        assert len(restored.accounts) == 1
        assert restored.accounts[0].id == "acc-1"
        assert restored.default_account_id == "acc-1"
        assert restored.window_width == 1400
        assert restored.window_height == 900


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_load_nonexistent_config(self):
        """Test loading config when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager()
            manager.config_file = Path(tmpdir) / "config.json"

            config = manager.load()

            assert config.accounts == []
            assert config.default_account_id is None

    def test_save_and_load_config(self):
        """Test saving and loading config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager()
            manager.config_file = Path(tmpdir) / "config.json"
            manager._config = AppConfig(
                window_width=1500,
                window_height=1000,
            )

            manager.save()

            # Load in new manager
            manager2 = ConfigManager()
            manager2.config_file = Path(tmpdir) / "config.json"
            config = manager2.load()

            assert config.window_width == 1500
            assert config.window_height == 1000

    def test_add_account(self):
        """Test adding an account."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager()
            manager.config_file = Path(tmpdir) / "config.json"
            manager._config = AppConfig()

            account = AccountConfig(
                id="acc-1",
                name="Test",
                email="test@example.com",
                imap_server="imap.example.com",
            )

            manager.add_account(account)

            assert len(manager.config.accounts) == 1
            assert manager.config.default_account_id == "acc-1"
            assert manager.config_file.exists()

    def test_remove_account(self):
        """Test removing an account."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager()
            manager.config_file = Path(tmpdir) / "config.json"

            account = AccountConfig(
                id="acc-1",
                name="Test",
                email="test@example.com",
                imap_server="imap.example.com",
            )

            manager._config = AppConfig(
                accounts=[account],
                default_account_id="acc-1",
            )

            manager.remove_account("acc-1")

            assert len(manager.config.accounts) == 0
            assert manager.config.default_account_id is None
