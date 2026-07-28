"""ViewModel for the chat view.

Manages the message list, streaming state, and provides
all chat interaction slots (send, stop, regenerate, edit, delete, copy).
"""

from typing import List, Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

from ..models.message import Message
from ..services.chat_service import ChatService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ChatVM(QObject):
    """ViewModel for the main chat area.

    Manages the list of messages displayed in the chat view,
    handles streaming state, and exposes chat actions as slots.

    Signals:
        messages_changed: Message list updated.
        streaming_changed: Streaming state changed.
        error_occurred: An error message to display.
        scroll_to_bottom: Request scroll in QML.
    """

    messages_changed = Signal()
    streaming_changed = Signal()
    error_occurred = Signal(str)
    scroll_to_bottom = Signal()

    def __init__(self, chat_service: ChatService, parent: Optional[QObject] = None) -> None:
        """Initialize ChatVM.

        Args:
            chat_service: Chat business logic service.
            parent: Qt parent object.
        """
        super().__init__(parent)
        self._service = chat_service
        self._messages: List[Message] = []
        self._is_streaming: bool = False
        self._current_conv_id: int = -1
        self._streaming_content: str = ""

    # ── Properties ──────────────────────────────────────────────

    def _get_messages(self) -> list:
        """Get messages as list of dicts for QML ListView."""
        result = []
        for i, msg in enumerate(self._messages):
            d = msg.to_dict()
            # Mark the last AI message as streaming
            if self._is_streaming and msg.role == "assistant" and i == len(self._messages) - 1:
                d["streaming"] = True
            else:
                d["streaming"] = False
            result.append(d)
        return result

    messages = Property(
        "QVariantList",
        _get_messages,
        notify=messages_changed,
    )

    def _get_streaming(self) -> bool:
        return self._is_streaming

    is_streaming = Property(
        bool,
        _get_streaming,
        notify=streaming_changed,
    )

    # ── Slots ───────────────────────────────────────────────────

    @Slot(int)
    def load_messages(self, conv_id: int) -> None:
        """Load messages for a conversation.

        Args:
            conv_id: Conversation ID.
        """
        if conv_id <= 0:
            self._messages = []
            self._current_conv_id = -1
            self.messages_changed.emit()
            return

        try:
            self._messages = self._service.get_messages(conv_id)
            self._current_conv_id = conv_id
            self.messages_changed.emit()
            self.scroll_to_bottom.emit()
            logger.debug("Loaded %d messages for conv %d", len(self._messages), conv_id)
        except Exception as e:
            logger.exception("Failed to load messages: %s", e)
            self.error_occurred.emit(f"Failed to load messages: {e}")

    @Slot(str)
    def send_message(self, content: str) -> None:
        """Send a user message and start streaming the response.

        Args:
            content: User's message text.
        """
        if not content.strip() or self._is_streaming:
            return
        if self._current_conv_id <= 0:
            self.error_occurred.emit("No conversation selected")
            return

        self._set_streaming(True)

        # Append user message immediately for instant feedback
        user_msg = Message(
            id=-len(self._messages) - 1,  # temporary negative ID
            conversation_id=self._current_conv_id,
            role="user",
            content=content,
        )
        self._messages.append(user_msg)
        self.messages_changed.emit()
        self.scroll_to_bottom.emit()

        # Append placeholder for AI response
        ai_placeholder = Message(
            id=-len(self._messages) - 1,
            conversation_id=self._current_conv_id,
            role="assistant",
            content="",
        )
        self._messages.append(ai_placeholder)
        self._streaming_content = ""
        self.messages_changed.emit()

        # Start streaming
        self._service.send_message(
            conv_id=self._current_conv_id,
            content=content,
            on_chunk=self._on_chunk,
            on_done=self._on_done,
            on_error=self._on_error,
        )

    def _on_chunk(self, content_delta: str) -> None:
        """Handle streaming content delta."""
        self._streaming_content += content_delta
        # Update the last message (AI placeholder) in-place
        if self._messages and self._messages[-1].role == "assistant":
            self._messages[-1].content = self._streaming_content
        self.messages_changed.emit()

    def _on_done(self, full_content: str) -> None:
        """Handle stream completion."""
        # Replace placeholder with actual persited message
        try:
            if self._current_conv_id > 0:
                self._messages = self._service.get_messages(self._current_conv_id)
        except Exception:
            pass
        self._streaming_content = ""
        self._set_streaming(False)
        self.messages_changed.emit()

    def _on_error(self, error: str) -> None:
        """Handle stream error."""
        # Update placeholder with error info
        if self._messages and self._messages[-1].role == "assistant":
            self._messages[-1].content = f"❌ Error: {error}"
        self._streaming_content = ""
        self._set_streaming(False)
        self.messages_changed.emit()
        self.error_occurred.emit(error)

    @Slot()
    def stop_generation(self) -> None:
        """Stop the current generation."""
        if self._is_streaming:
            self._service.stop_generation()

    @Slot()
    def regenerate(self) -> None:
        """Regenerate the last assistant response."""
        if self._is_streaming or self._current_conv_id <= 0:
            return

        self._set_streaming(True)

        # Append placeholder
        ai_placeholder = Message(
            id=-len(self._messages) - 1,
            conversation_id=self._current_conv_id,
            role="assistant",
            content="",
        )
        self._messages.append(ai_placeholder)
        self._streaming_content = ""
        self.messages_changed.emit()

        self._service.regenerate_last(
            conv_id=self._current_conv_id,
            on_chunk=self._on_chunk,
            on_done=self._on_done,
            on_error=self._on_error,
        )

    @Slot(int, str)
    def edit_and_resend(self, msg_id: int, new_content: str) -> None:
        """Edit a user message and regenerate from that point.

        Args:
            msg_id: Message ID to edit.
            new_content: New message content.
        """
        if self._is_streaming or self._current_conv_id <= 0:
            return

        self._set_streaming(True)

        ai_placeholder = Message(
            id=-len(self._messages) - 1,
            conversation_id=self._current_conv_id,
            role="assistant",
            content="",
        )
        self._messages.append(ai_placeholder)
        self._streaming_content = ""
        self.messages_changed.emit()

        self._service.edit_and_resend(
            conv_id=self._current_conv_id,
            msg_id=msg_id,
            new_content=new_content,
            on_chunk=self._on_chunk,
            on_done=self._on_done,
            on_error=self._on_error,
        )

    @Slot(int)
    def delete_message(self, msg_id: int) -> None:
        """Delete a single message.

        Args:
            msg_id: Message ID.
        """
        try:
            self._service.delete_message(msg_id)
            self._messages = [m for m in self._messages if m.id != msg_id]
            self.messages_changed.emit()
        except Exception as e:
            logger.exception("Failed to delete message: %s", e)

    @Slot(str)
    def copy_message(self, content: str) -> None:
        """Copy message content to clipboard.

        Args:
            content: Text to copy.
        """
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(content)
        logger.debug("Copied to clipboard: %d chars", len(content))

    def _set_streaming(self, streaming: bool) -> None:
        """Set streaming state and emit signal.

        Args:
            streaming: New streaming state.
        """
        if self._is_streaming != streaming:
            self._is_streaming = streaming
            self.streaming_changed.emit()
