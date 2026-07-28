"""Configuration file reader/writer for config.json.

Handles persistence of AppConfig with atomic writes and error recovery.
"""

import json
from pathlib import Path
from typing import Optional

from ..models.app_config import AppConfig
from ..utils.constants import CONFIG_FILE, CONFIG_DIR
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages reading and writing of config.json.

    Provides atomic write (write-to-temp-then-rename) to prevent corruption,
    and graceful fallback to defaults if the config file is missing or malformed.

    Attributes:
        config_path: Path to the config.json file.
        _config: In-memory AppConfig instance.
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize ConfigManager.

        Args:
            config_path: Override default config file path (for testing).
        """
        self.config_path: Path = config_path or CONFIG_FILE
        self._config: AppConfig = AppConfig()

    def load(self) -> AppConfig:
        """Load configuration from disk.

        Returns:
            AppConfig instance. Falls back to defaults on any error.

        Raises:
            FileNotFoundError: Only if config is missing and create_if_missing is disabled.
        """
        if not self.config_path.exists():
            logger.info("Config file not found, creating with defaults: %s", self.config_path)
            self._config = AppConfig()
            self.save()
            return self._config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._config = AppConfig.from_dict(data)
            logger.info("Config loaded from %s", self.config_path)
            return self._config
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("Failed to parse config, using defaults: %s", e)
            self._config = AppConfig()
            return self._config
        except OSError as e:
            logger.error("Failed to read config file: %s", e)
            self._config = AppConfig()
            return self._config

    def save(self, config: Optional[AppConfig] = None) -> None:
        """Save configuration to disk atomically.

        Uses write-to-temp-file-then-rename strategy to prevent corruption
        on unexpected termination.

        Args:
            config: AppConfig to save. If None, saves current in-memory config.
        """
        if config is not None:
            self._config = config

        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = self._config.to_dict()
        temp_path = self.config_path.with_suffix(".tmp")

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_path.replace(self.config_path)
            logger.info("Config saved to %s", self.config_path)
        except OSError as e:
            logger.error("Failed to save config: %s", e)
            raise

    @property
    def config(self) -> AppConfig:
        """Get current configuration (in-memory)."""
        return self._config

    def get(self, key: str) -> str:
        """Get a single config value by key.

        Args:
            key: Config attribute name.

        Returns:
            String value of the config key.
        """
        return str(getattr(self._config, key, ""))

    def set(self, key: str, value: str) -> None:
        """Set a single config value and persist immediately.

        Args:
            key: Config attribute name.
            value: New value (will be type-coerced to match the field type).
        """
        if not hasattr(self._config, key):
            raise AttributeError(f"Unknown config key: {key}")

        # Type coercion based on the default value's type
        default_type = type(getattr(AppConfig(), key))
        if default_type is bool:
            coerced = value.lower() in ("true", "1", "yes") if isinstance(value, str) else bool(value)
        elif default_type is int:
            coerced = int(value)
        else:
            coerced = str(value)

        setattr(self._config, key, coerced)
        self.save()
