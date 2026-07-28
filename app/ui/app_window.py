"""Main application window management.

Orchestrates the creation of all services, viewmodels, and the QML UI.
This is the wiring layer — all dependency injection happens here.
"""

from pathlib import Path

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QGuiApplication, QFont

from ..config.config_manager import ConfigManager
from ..database.conversation_repo import ConversationRepo
from ..database.db_manager import DatabaseManager
from ..database.message_repo import MessageRepo
from ..services.chat_service import ChatService
from ..services.config_service import ConfigService
from ..services.model_service import ModelService
from ..services.ollama_client import OllamaClient
from ..services.session_service import SessionService
from ..utils.logger import get_logger, setup_logging
from ..viewmodels.chat_vm import ChatVM
from ..viewmodels.model_selector_vm import ModelSelectorVM
from ..viewmodels.session_list_vm import SessionListVM
from ..viewmodels.settings_vm import SettingsVM
from .qml_bridge import QMLBridge

logger = get_logger(__name__)


class AppWindow(QObject):
    """Main application orchestrator.

    Creates the QML bridge, initializes all services and viewmodels,
    and wires them together. This is the single entry point for the app.

    Usage:
        app = QGuiApplication(sys.argv)
        window = AppWindow()
        window.initialize()
        app.exec()
    """

    def __init__(self) -> None:
        """Initialize AppWindow (does not start the app yet)."""
        super().__init__()
        self._bridge = QMLBridge()

        # These are created in initialize()
        self.db: DatabaseManager | None = None
        self.config_manager: ConfigManager | None = None
        self.ollama_client: OllamaClient | None = None

        # Services
        self.config_service: ConfigService | None = None
        self.session_service: SessionService | None = None
        self.chat_service: ChatService | None = None
        self.model_service: ModelService | None = None

        # ViewModels
        self.session_list_vm: SessionListVM | None = None
        self.chat_vm: ChatVM | None = None
        self.settings_vm: SettingsVM | None = None
        self.model_selector_vm: ModelSelectorVM | None = None

    def initialize(self, app: QGuiApplication) -> None:
        """Wire everything together and start the QML UI.

        Args:
            app: The running QGuiApplication instance.
        """
        logger.info("Initializing RemoteOllama application...")

        # ── 1. Infrastructure ─────────────────────────────────
        self.db = DatabaseManager()
        self.db.migrate()

        self.config_manager = ConfigManager()
        config = self.config_manager.load()

        self.ollama_client = OllamaClient(
            base_url=config.server_url,
            timeout=config.timeout,
        )

        # ── 2. Repositories ───────────────────────────────────
        conv_repo = ConversationRepo(self.db)
        msg_repo = MessageRepo(self.db)

        # ── 3. Services ───────────────────────────────────────
        self.config_service = ConfigService(self.config_manager)
        self.session_service = SessionService(conv_repo, msg_repo)
        self.chat_service = ChatService(conv_repo, msg_repo, self.ollama_client)
        self.model_service = ModelService(self.ollama_client)

        # ── 4. ViewModels ─────────────────────────────────────
        self.session_list_vm = SessionListVM(self.session_service)
        self.chat_vm = ChatVM(self.chat_service)
        self.settings_vm = SettingsVM(self.config_service, self.ollama_client)
        self.model_selector_vm = ModelSelectorVM(self.model_service)

        # Connect session selection → message loading
        self.session_list_vm.current_session_changed.connect(self.chat_vm.load_messages)

        # ── 5. QML Bridge ─────────────────────────────────────
        self._bridge.initialize(app)

        # Register all ViewModels as QML context properties
        self._bridge.register_context("sessionListVM", self.session_list_vm)
        self._bridge.register_context("chatVM", self.chat_vm)
        self._bridge.register_context("settingsVM", self.settings_vm)
        self._bridge.register_context("modelSelectorVM", self.model_selector_vm)

        # ── 6. Load MainWindow QML ────────────────────────────
        self._bridge.load_main("MainWindow.qml")

        # ── 7. Initial data load ──────────────────────────────
        self.session_list_vm.load_sessions()

        # If a session exists, select the most recent one
        sessions = self.session_list_vm._get_sessions()
        if sessions:
            first_id = sessions[0]["id"]
            self.session_list_vm.select_session(first_id)

        # Pre-fetch models
        try:
            self.model_selector_vm.fetch_models()
        except Exception as e:
            logger.warning("Could not pre-fetch models: %s", e)

        logger.info("RemoteOllama initialized successfully")

    def cleanup(self) -> None:
        """Clean up resources on application exit."""
        logger.info("Shutting down...")
        if self.ollama_client:
            self.ollama_client.close()
        if self.db:
            self.db.close()
        logger.info("RemoteOllama stopped")
