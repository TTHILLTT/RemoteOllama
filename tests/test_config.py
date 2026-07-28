"""Unit tests for ConfigManager and AppConfig."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from app.config.config_manager import ConfigManager
from app.models.app_config import AppConfig


class TestAppConfig:
    """Tests for AppConfig model."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = AppConfig()
        assert config.server_url == "http://localhost:11434"
        assert config.timeout == 60
        assert config.streaming_enabled is True
        assert config.theme == "dark"
        assert config.font_size == 14

    def test_from_dict_partial(self):
        """Test that from_dict fills missing keys with defaults."""
        data = {"server_url": "http://custom:11434"}
        config = AppConfig.from_dict(data)
        assert config.server_url == "http://custom:11434"
        assert config.theme == "dark"  # default
        assert config.font_size == 14  # default

    def test_validate_valid(self):
        """Test validation of valid config."""
        config = AppConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_invalid_url(self):
        """Test validation catches invalid URL."""
        config = AppConfig(server_url="not-a-url")
        errors = config.validate()
        assert any("http" in e.lower() for e in errors)

    def test_validate_invalid_timeout(self):
        """Test validation catches invalid timeout."""
        config = AppConfig(timeout=0)
        errors = config.validate()
        assert any("timeout" in e.lower() for e in errors)

        config.timeout = 601
        errors = config.validate()
        assert any("timeout" in e.lower() for e in errors)

    def test_validate_invalid_theme(self):
        """Test validation catches invalid theme."""
        config = AppConfig(theme="blue")
        errors = config.validate()
        assert any("theme" in e.lower() for e in errors)

    def test_to_dict_roundtrip(self):
        """Test that to_dict and from_dict are symmetric."""
        original = AppConfig(
            server_url="http://192.168.1.20:11434",
            default_model="qwen3:14b",
            timeout=120,
            streaming_enabled=False,
            theme="light",
            font_size=18,
        )
        data = original.to_dict()
        restored = AppConfig.from_dict(data)
        assert restored.server_url == original.server_url
        assert restored.default_model == original.default_model
        assert restored.timeout == original.timeout
        assert restored.streaming_enabled == original.streaming_enabled
        assert restored.theme == original.theme
        assert restored.font_size == original.font_size


class TestConfigManager:
    """Tests for ConfigManager file operations."""

    @pytest.fixture
    def temp_config_path(self):
        """Create a temporary config file path."""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        path = Path(path)
        yield path
        # Cleanup
        try:
            os.unlink(path)
            os.unlink(path.with_suffix(".tmp"))
        except OSError:
            pass

    def test_save_and_load(self, temp_config_path):
        """Test saving and loading configuration."""
        manager = ConfigManager(config_path=temp_config_path)
        config = AppConfig(server_url="http://example.com:11434", theme="light")
        manager.save(config)
        manager.load()

        loaded = manager.config
        assert loaded.server_url == "http://example.com:11434"
        assert loaded.theme == "light"

    def test_load_missing_file_creates_default(self, temp_config_path):
        """Test that missing config file creates one with defaults."""
        # Ensure file doesn't exist
        if temp_config_path.exists():
            temp_config_path.unlink()

        manager = ConfigManager(config_path=temp_config_path)
        config = manager.load()

        assert config.server_url == "http://localhost:11434"  # default
        assert temp_config_path.exists()  # file was created

    def test_load_malformed_json(self, temp_config_path):
        """Test that malformed JSON falls back to defaults."""
        temp_config_path.write_text("{ this is not valid json }")
        manager = ConfigManager(config_path=temp_config_path)
        config = manager.load()

        assert config.server_url == "http://localhost:11434"  # default

    def test_set_and_save(self, temp_config_path):
        """Test setting individual config values."""
        manager = ConfigManager(config_path=temp_config_path)
        manager.load()
        manager.set("server_url", "http://new-server:11434")
        manager.set("timeout", "30")

        # Reload from disk
        manager.load()
        assert manager.config.server_url == "http://new-server:11434"
        assert manager.config.timeout == 30
