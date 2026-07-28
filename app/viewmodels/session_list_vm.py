"""ViewModel for the session (conversation) list in the sidebar.

Exposes the list of conversations to QML via Qt properties,
and handles session CRUD operations triggered from the UI.
"""

from typing import List, Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

from ..models.conversation import Conversation
from ..services.session_service import SessionService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SessionListVM(QObject):
    """ViewModel for the sidebar session list.

    Exposes a list of conversations as QML-compatible data and
    provides slots for CRUD operations.

    Signals:
        sessions_changed: Emitted when the session list changes.
        current_session_changed: Emitted with the newly selected session ID.
    """

    sessions_changed = Signal()
    current_session_changed = Signal(int)

    def __init__(self, session_service: SessionService, parent: Optional[QObject] = None) -> None:
        """Initialize SessionListVM.

        Args:
            session_service: Session business logic service.
            parent: Qt parent object.
        """
        super().__init__(parent)
        self._service = session_service
        self._sessions: List[Conversation] = []
        self._current_session_id: int = -1

    # ── Properties ──────────────────────────────────────────────

    def _get_sessions(self) -> list:
        """Get sessions as list of dicts for QML ListView."""
        return [s.to_dict() for s in self._sessions]

    sessions = Property(
        "QVariantList",
        _get_sessions,
        notify=sessions_changed,
    )

    def _get_current_id(self) -> int:
        return self._current_session_id

    current_session_id = Property(
        int,
        _get_current_id,
        notify=current_session_changed,
    )

    # ── Slots ───────────────────────────────────────────────────

    @Slot()
    def load_sessions(self) -> None:
        """Load all sessions from the database."""
        try:
            self._sessions = self._service.get_sessions()
            self.sessions_changed.emit()
            logger.debug("Loaded %d sessions", len(self._sessions))
        except Exception as e:
            logger.exception("Failed to load sessions: %s", e)

    @Slot(str, str, result=int)
    def create_session(self, model: str = "", title: str = "New Chat") -> int:
        """Create a new session.

        Args:
            model: Model name for the session.
            title: Initial session title.

        Returns:
            The new session ID.
        """
        try:
            conv = self._service.create_session(model=model, title=title)
            self._sessions.insert(0, conv)
            self.sessions_changed.emit()
            self.select_session(conv.id)
            logger.info("Created session %d", conv.id)
            return conv.id
        except Exception as e:
            logger.exception("Failed to create session: %s", e)
            return -1

    @Slot(int)
    def select_session(self, conv_id: int) -> None:
        """Select a session by ID (triggers chat loading).

        Args:
            conv_id: Session ID to select.
        """
        if self._current_session_id != conv_id:
            self._current_session_id = conv_id
            self.current_session_changed.emit(conv_id)
            logger.debug("Selected session %d", conv_id)

    @Slot(int)
    def delete_session(self, conv_id: int) -> None:
        """Delete a session and its messages.

        Args:
            conv_id: Session ID to delete.
        """
        try:
            self._service.delete_session(conv_id)
            self._sessions = [s for s in self._sessions if s.id != conv_id]
            if self._current_session_id == conv_id:
                self._current_session_id = -1 if not self._sessions else self._sessions[0].id
                if self._current_session_id > 0:
                    self.current_session_changed.emit(self._current_session_id)
            self.sessions_changed.emit()
            logger.info("Deleted session %d", conv_id)
        except Exception as e:
            logger.exception("Failed to delete session: %s", e)

    @Slot(int, str)
    def rename_session(self, conv_id: int, title: str) -> None:
        """Rename a session.

        Args:
            conv_id: Session ID.
            title: New title.
        """
        try:
            self._service.rename_session(conv_id, title)
            for s in self._sessions:
                if s.id == conv_id:
                    s.title = title
                    break
            self.sessions_changed.emit()
        except Exception as e:
            logger.exception("Failed to rename session: %s", e)

    @Slot(int, str, result=int)
    def duplicate_session(self, conv_id: int, new_model: str = "") -> int:
        """Duplicate a session, optionally changing the model.

        Args:
            conv_id: Source session ID.
            new_model: New model name (empty = keep original).

        Returns:
            New session ID.
        """
        try:
            new_conv = self._service.duplicate_session(
                conv_id,
                new_model if new_model else None,
            )
            if new_conv:
                self._sessions.insert(0, new_conv)
                self.sessions_changed.emit()
                self.select_session(new_conv.id)
                return new_conv.id
        except Exception as e:
            logger.exception("Failed to duplicate session: %s", e)
        return -1

    @Slot(int, result="QVariant")
    def get_session(self, conv_id: int) -> dict:
        """Get a single session's data.

        Args:
            conv_id: Session ID.

        Returns:
            Session dict, or empty dict if not found.
        """
        conv = self._service.get_session(conv_id)
        return conv.to_dict() if conv else {}
