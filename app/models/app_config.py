"""Application configuration data model."""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class AppConfig:
    """Application-wide configuration.

    Persisted to config.json. All fields have sensible defaults.

    Attributes:
        server_url: Ollama server base URL (e.g., 'http://192.168.1.20:11434').
        default_model: Default model name to pre-select.
        timeout: HTTP request timeout in seconds.
        streaming_enabled: Whether to use streaming by default.
        theme: UI theme: 'dark' or 'light'.
        font_size: Base font size in points.
        max_context_messages: Maximum messages to include in context.
    """

    server_url: str = "http://localhost:11434"
    default_model: str = ""
    timeout: int = 60
    streaming_enabled: bool = True
    theme: str = "dark"
    font_size: int = 14
    max_context_messages: int = 50

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        """Create instance from dictionary, filling defaults for missing keys."""
        defaults = cls()
        merged = {
            "server_url": data.get("server_url", defaults.server_url),
            "default_model": data.get("default_model", defaults.default_model),
            "timeout": data.get("timeout", defaults.timeout),
            "streaming_enabled": data.get("streaming_enabled", defaults.streaming_enabled),
            "theme": data.get("theme", defaults.theme),
            "font_size": data.get("font_size", defaults.font_size),
            "max_context_messages": data.get("max_context_messages", defaults.max_context_messages),
        }
        return cls(**merged)

    def validate(self) -> list[str]:
        """Validate configuration values.

        Returns:
            List of error messages; empty list means valid.
        """
        errors = []
        if not self.server_url:
            errors.append("Server URL cannot be empty")
        elif not self.server_url.startswith(("http://", "https://")):
            errors.append("Server URL must start with http:// or https://")
        if self.timeout < 1 or self.timeout > 600:
            errors.append("Timeout must be between 1 and 600 seconds")
        if self.theme not in ("dark", "light"):
            errors.append("Theme must be 'dark' or 'light'")
        if self.font_size < 8 or self.font_size > 48:
            errors.append("Font size must be between 8 and 48")
        return errors
