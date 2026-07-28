"""ViewModel for the settings page.

Exposes config values as Qt properties and provides slots
for reading, writing, and testing settings.
"""

from typing import Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

from ..services.config_service import ConfigService
from ..services.ollama_client import OllamaClient
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SettingsVM(QObject):
    """ViewModel for application settings.

    Exposes all configurable values as Qt properties with
    change notification signals.

    Signals:
        server_url_changed: Server URL updated.
        theme_changed: Theme setting updated.
        font_size_changed: Font size updated.
        connection_test_result: Result of connection test.
    """

    server_url_changed = Signal()
    default_model_changed = Signal()
    timeout_changed = Signal()
    streaming_changed_signal = Signal()
    theme_changed = Signal()
    font_size_changed = Signal()
    connection_test_result = Signal(bool, str)

    def __init__(
        self,
        config_service: ConfigService,
        client: Optional[OllamaClient] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        """Initialize SettingsVM.

        Args:
            config_service: Configuration business service.
            client: OllamaClient for connection testing.
            parent: Qt parent.
        """
        super().__init__(parent)
        self._config_service = config_service
        self._client = client

    # ── Server URL ──────────────────────────────────────────────

    def _get_server_url(self) -> str:
        return self._config_service.get_server_url()

    def _set_server_url(self, url: str) -> None:
        try:
            self._config_service.set_server_url(url)
            self.server_url_changed.emit()
        except ValueError as e:
            logger.warning("Invalid server URL: %s", e)

    server_url = Property(str, _get_server_url, _set_server_url, notify=server_url_changed)

    # ── Default Model ───────────────────────────────────────────

    def _get_default_model(self) -> str:
        return self._config_service.get_config().default_model

    def _set_default_model(self, model: str) -> None:
        self._config_service.config_manager.set("default_model", model)
        self.default_model_changed.emit()

    default_model = Property(str, _get_default_model, _set_default_model, notify=default_model_changed)

    # ── Timeout ─────────────────────────────────────────────────

    def _get_timeout(self) -> int:
        return self._config_service.get_timeout()

    def _set_timeout(self, timeout: int) -> None:
        self._config_service.set_timeout(timeout)
        self.timeout_changed.emit()

    timeout = Property(int, _get_timeout, _set_timeout, notify=timeout_changed)

    # ── Streaming ───────────────────────────────────────────────

    def _get_streaming(self) -> bool:
        return self._config_service.is_streaming_enabled()

    def _set_streaming(self, enabled: bool) -> None:
        self._config_service.set_streaming_enabled(enabled)
        self.streaming_changed_signal.emit()

    streaming_enabled = Property(bool, _get_streaming, _set_streaming, notify=streaming_changed_signal)

    # ── Theme ───────────────────────────────────────────────────

    def _get_theme(self) -> str:
        return self._config_service.get_theme()

    def _set_theme(self, theme: str) -> None:
        try:
            self._config_service.set_theme(theme)
            self.theme_changed.emit()
        except ValueError as e:
            logger.warning("Invalid theme: %s", e)

    theme = Property(str, _get_theme, _set_theme, notify=theme_changed)

    # ── Font Size ───────────────────────────────────────────────

    def _get_font_size(self) -> int:
        return self._config_service.get_font_size()

    def _set_font_size(self, size: int) -> None:
        try:
            self._config_service.set_font_size(size)
            self.font_size_changed.emit()
        except ValueError as e:
            logger.warning("Invalid font size: %s", e)

    font_size = Property(int, _get_font_size, _set_font_size, notify=font_size_changed)

    # ── Slots ───────────────────────────────────────────────────

    @Slot()
    def load_settings(self) -> None:
        """Reload settings from disk and notify all properties."""
        self._config_service.config_manager.load()
        self.server_url_changed.emit()
        self.default_model_changed.emit()
        self.timeout_changed.emit()
        self.streaming_changed_signal.emit()
        self.theme_changed.emit()
        self.font_size_changed.emit()
        logger.info("Settings loaded")

    @Slot()
    def save_settings(self) -> None:
        """Persist current settings to disk."""
        try:
            self._config_service.config_manager.save()
            logger.info("Settings saved")
            self.connection_test_result.emit(True, "Settings saved successfully")
        except Exception as e:
            logger.exception("Failed to save settings")
            self.connection_test_result.emit(False, f"Failed to save: {e}")

    @Slot()
    def test_connection(self) -> None:
        """Test connection to the configured Ollama server."""
        url = self._config_service.get_server_url()
        timeout = self._config_service.get_timeout()

        if not url:
            self.connection_test_result.emit(False, "Server URL is not set")
            return

        try:
            # Create a temporary client for testing
            test_client = OllamaClient(base_url=url, timeout=timeout)
            if test_client.health():
                version = test_client.version()
                self.connection_test_result.emit(True, f"Connected! Ollama {version}")
            else:
                self.connection_test_result.emit(False, "Server did not respond")
            test_client.close()
        except Exception as e:
            logger.warning("Connection test failed: %s", e)
            self.connection_test_result.emit(False, f"Connection failed: {e}")
