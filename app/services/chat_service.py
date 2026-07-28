"""Chat orchestration service.

Manages the full lifecycle of a chat interaction:
message persistence, context building, streaming, and regeneration.
"""

import threading
from typing import Callable, Generator, List, Optional

from ..database.conversation_repo import ConversationRepo
from ..database.message_repo import MessageRepo
from ..models.conversation import Conversation
from ..models.message import Message, MessageRole
from ..utils.logger import get_logger
from .ollama_client import OllamaClient, OllamaError

logger = get_logger(__name__)

# Type alias for streaming callback
ChunkCallback = Callable[[str], None]
ErrorCallback = Callable[[str], None]
DoneCallback = Callable[[str], None]


class ChatService:
    """Orchestrates chat interactions between UI, database, and Ollama API.

    Handles:
    - Sending messages with streaming
    - Context window management
    - Regeneration of responses
    - Message editing and deletion

    Attributes:
        conv_repo: Conversation data access.
        msg_repo: Message data access.
        client: Ollama HTTP client.
        _stop_event: Threading event for stopping generation.
        _current_thread: Reference to the current streaming thread.
    """

    def __init__(
        self,
        conv_repo: ConversationRepo,
        msg_repo: MessageRepo,
        client: OllamaClient,
    ) -> None:
        """Initialize ChatService.

        Args:
            conv_repo: Conversation repository.
            msg_repo: Message repository.
            client: Ollama API client.
        """
        self.conv_repo = conv_repo
        self.msg_repo = msg_repo
        self.client = client
        self._stop_event = threading.Event()
        self._current_thread: Optional[threading.Thread] = None

    def send_message(
        self,
        conv_id: int,
        content: str,
        on_chunk: ChunkCallback,
        on_done: DoneCallback,
        on_error: ErrorCallback,
        max_context: int = 50,
    ) -> None:
        """Send a user message and stream the AI response.

        This method:
        1. Saves the user message
        2. Auto-titles the conversation if it's the first message
        3. Builds the messages context array
        4. Sends to Ollama API with streaming
        5. Calls on_chunk for each token, on_done when complete

        The actual streaming runs in a background thread to avoid
        blocking the caller. This method returns immediately.

        Args:
            conv_id: Conversation ID.
            content: User's message text.
            on_chunk: Called with each content delta (str).
            on_done: Called with the full response when complete.
            on_error: Called with error message on failure.
            max_context: Maximum messages to include in context.
        """
        # 1. Save user message
        user_msg = self.msg_repo.add(conv_id, "user", content)

        # 2. Auto-title on first message
        msg_count = self.msg_repo.count(conv_id)
        if msg_count <= 2:  # Only user message so far (+ possibly system)
            self.conv_repo.update_title(
                conv_id,
                content.strip().replace("\n", " ")[:50] or "New Chat",
            )

        # 3. Get conversation for model info
        conv = self.conv_repo.get_by_id(conv_id)
        if conv is None:
            on_error("Conversation not found")
            return

        model = conv.model
        if not model:
            on_error("No model selected for this conversation")
            return

        # 4. Build messages array
        api_messages = self._build_messages_array(conv_id, max_context)

        # 5. Stream in background thread
        self._stop_event.clear()
        thread = threading.Thread(
            target=self._stream_task,
            args=(conv_id, model, api_messages, on_chunk, on_done, on_error),
            daemon=True,
        )
        self._current_thread = thread
        thread.start()

    def _build_messages_array(self, conv_id: int, max_context: int) -> List[dict]:
        """Build the full messages array for /api/chat.

        Includes the system prompt (if set) and the most recent messages.

        Args:
            conv_id: Conversation ID.
            max_context: Maximum recent messages to include.

        Returns:
            List of message dicts ready for the API.
        """
        conv = self.conv_repo.get_by_id(conv_id)
        messages: List[dict] = []

        # Add system prompt if configured
        if conv and conv.system_prompt:
            messages.append({"role": "system", "content": conv.system_prompt})

        # Add recent messages
        recent = self.msg_repo.get_last_n(conv_id, max_context)
        messages.extend(msg.to_api_format() for msg in recent)

        logger.debug("Built messages array: %d total for conv %d", len(messages), conv_id)
        return messages

    def _stream_task(
        self,
        conv_id: int,
        model: str,
        api_messages: List[dict],
        on_chunk: ChunkCallback,
        on_done: DoneCallback,
        on_error: ErrorCallback,
    ) -> None:
        """Background task that handles the streaming HTTP request.

        Args:
            conv_id: Conversation ID.
            model: Model name.
            api_messages: Messages in API format.
            on_chunk: Callback per token.
            on_done: Callback on completion.
            on_error: Callback on error.
        """
        full_content: List[str] = []
        try:
            for chunk in self.client.chat(model, api_messages, stream=True):
                if self._stop_event.is_set():
                    logger.info("Generation stopped by user")
                    # Save partial content
                    partial = "".join(full_content)
                    if partial:
                        self.msg_repo.add(conv_id, "assistant", partial + "\n\n[已停止]")
                    on_done(partial)
                    return

                message = chunk.get("message", {})
                content_delta = message.get("content", "")

                if content_delta:
                    full_content.append(content_delta)
                    on_chunk(content_delta)

            # Stream complete — save final message
            complete = "".join(full_content)
            self.msg_repo.add(conv_id, "assistant", complete)
            self.conv_repo.touch(conv_id)
            logger.info("Stream complete: %d chars for conv %d", len(complete), conv_id)
            on_done(complete)

        except OllamaError as e:
            logger.error("Ollama error during streaming: %s", e)
            on_error(str(e))
        except Exception as e:
            logger.exception("Unexpected error during streaming")
            on_error(f"Unexpected error: {e}")

    def stop_generation(self) -> None:
        """Stop the current streaming generation.

        Sets the stop event and cancels the HTTP request.
        Does not block — the stream thread will finish asynchronously.
        """
        logger.info("Stop requested")
        self._stop_event.set()
        self.client.stop()

    def regenerate_last(
        self,
        conv_id: int,
        on_chunk: ChunkCallback,
        on_done: DoneCallback,
        on_error: ErrorCallback,
        max_context: int = 50,
    ) -> None:
        """Regenerate the last assistant response.

        Deletes the last assistant message (if present), then re-sends
        the conversation context to generate a new response.

        Args:
            conv_id: Conversation ID.
            on_chunk: Called with each content delta.
            on_done: Called with the full response.
            on_error: Called on error.
            max_context: Maximum context messages.
        """
        messages = self.msg_repo.get_last_n(conv_id, max_context)
        if messages and messages[-1].role == "assistant":
            self.msg_repo.delete(messages[-1].id)
            logger.info("Deleted last assistant message for regeneration")

        conv = self.conv_repo.get_by_id(conv_id)
        if conv is None:
            on_error("Conversation not found")
            return

        model = conv.model
        if not model:
            on_error("No model selected")
            return

        api_messages = self._build_messages_array(conv_id, max_context)

        self._stop_event.clear()
        thread = threading.Thread(
            target=self._stream_task,
            args=(conv_id, model, api_messages, on_chunk, on_done, on_error),
            daemon=True,
        )
        self._current_thread = thread
        thread.start()

    def edit_and_resend(
        self,
        conv_id: int,
        msg_id: int,
        new_content: str,
        on_chunk: ChunkCallback,
        on_done: DoneCallback,
        on_error: ErrorCallback,
        max_context: int = 50,
    ) -> None:
        """Edit a user message and regenerate from that point.

        Deletes the target message and all subsequent messages,
        then sends the edited content as a new user message.

        Args:
            conv_id: Conversation ID.
            msg_id: ID of the user message to edit.
            new_content: New content for the message.
            on_chunk: Called with each content delta.
            on_done: Called with the full response.
            on_error: Called on error.
            max_context: Maximum context messages.
        """
        # Delete from the edited message onward
        self.msg_repo.delete_from(conv_id, msg_id)

        # Now send as new
        self.send_message(conv_id, new_content, on_chunk, on_done, on_error, max_context)

    def get_messages(
        self, conv_id: int, limit: int = 50, offset: int = 0
    ) -> List[Message]:
        """Get messages for a conversation with pagination.

        Args:
            conv_id: Conversation ID.
            limit: Messages per page.
            offset: Page offset.

        Returns:
            List of Message objects.
        """
        return self.msg_repo.get_by_conv(conv_id, limit, offset)

    def delete_message(self, msg_id: int) -> None:
        """Delete a single message.

        Args:
            msg_id: Message ID.
        """
        self.msg_repo.delete(msg_id)

    def get_conversation(self, conv_id: int) -> Optional[Conversation]:
        """Get conversation details.

        Args:
            conv_id: Conversation ID.

        Returns:
            Conversation or None.
        """
        return self.conv_repo.get_by_id(conv_id)
