"""Configuration management service.

Provides a business-logic layer over ConfigManager for use by ViewModels.
"""

from typing import Optional

from ..config.config_manager import ConfigManager
from ..models.app_config import AppConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigService:
    """Business service for application configuration.

    Wraps ConfigManager to provide a stable API for ViewModels,
    with validation and event hooks for config changes.

    Attributes:
        config_manager: The underlying ConfigManager instance.
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None) -> None:
        """Initialize ConfigService.

        Args:
            config_manager: ConfigManager instance. Creates default if None.
        """
        self.config_manager = config_manager or ConfigManager()
        self.config_manager.load()

    def get_config(self) -> AppConfig:
        """Get the full application configuration.

        Returns:
            Current AppConfig.
        """
        return self.config_manager.config

    def get_server_url(self) -> str:
        """Get the configured server URL.

        Returns:
            Server URL string.
        """
        return self.config_manager.config.server_url

    def set_server_url(self, url: str) -> None:
        """Set the server URL and persist.

        Args:
            url: New server URL (must start with http:// or https://).

        Raises:
            ValueError: If URL format is invalid.
        """
        if not url.startswith(("http://", "https://")):
            raise ValueError("Server URL must start with http:// or https://")
        self.config_manager.set("server_url", url)
        logger.info("Server URL changed to %s", url)

    def get_theme(self) -> str:
        """Get current theme setting.

        Returns:
            'dark' or 'light'.
        """
        return self.config_manager.config.theme

    def set_theme(self, theme: str) -> None:
        """Set the UI theme.

        Args:
            theme: 'dark' or 'light'.

        Raises:
            ValueError: If theme is not 'dark' or 'light'.
        """
        if theme not in ("dark", "light"):
            raise ValueError("Theme must be 'dark' or 'light'")
        self.config_manager.set("theme", theme)
        logger.info("Theme changed to %s", theme)

    def get_font_size(self) -> int:
        """Get current font size.

        Returns:
            Font size in points.
        """
        return self.config_manager.config.font_size

    def set_font_size(self, size: int) -> None:
        """Set the font size.

        Args:
            size: Font size in points (8-48).

        Raises:
            ValueError: If size is out of range.
        """
        if size < 8 or size > 48:
            raise ValueError("Font size must be between 8 and 48")
        self.config_manager.set("font_size", size)
        logger.info("Font size changed to %d", size)

    def is_streaming_enabled(self) -> bool:
        """Check if streaming is enabled by default.

        Returns:
            True if streaming is enabled.
        """
        return self.config_manager.config.streaming_enabled

    def set_streaming_enabled(self, enabled: bool) -> None:
        """Enable or disable streaming by default.

        Args:
            enabled: Whether to enable streaming.
        """
        self.config_manager.set("streaming_enabled", enabled)
        logger.info("Streaming %s", "enabled" if enabled else "disabled")

    def get_timeout(self) -> int:
        """Get HTTP request timeout.

        Returns:
            Timeout in seconds.
        """
        return self.config_manager.config.timeout

    def set_timeout(self, timeout: int) -> None:
        """Set HTTP request timeout.

        Args:
            timeout: Timeout in seconds (1-600).

        Raises:
            ValueError: If timeout is out of range.
        """
        if timeout < 1 or timeout > 600:
            raise ValueError("Timeout must be between 1 and 600 seconds")
        self.config_manager.set("timeout", timeout)
        logger.info("Timeout changed to %ds", timeout)

    def validate(self) -> list[str]:
        """Validate current configuration.

        Returns:
            List of error messages (empty = valid).
        """
        return self.config_manager.config.validate()
