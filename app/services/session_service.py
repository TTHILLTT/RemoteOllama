"""Session (conversation) management service.

Orchestrates conversation CRUD operations with business rules
such as auto-titling and duplicate-with-model.
"""

from typing import List, Optional

from ..database.conversation_repo import ConversationRepo
from ..database.message_repo import MessageRepo
from ..models.conversation import Conversation
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SessionService:
    """Business logic for managing chat sessions (conversations).

    Handles creation, deletion, renaming, and duplication of sessions.

    Attributes:
        conv_repo: Conversation data access.
        msg_repo: Message data access (for duplication).
    """

    def __init__(self, conv_repo: ConversationRepo, msg_repo: MessageRepo) -> None:
        """Initialize SessionService.

        Args:
            conv_repo: Conversation repository.
            msg_repo: Message repository.
        """
        self.conv_repo = conv_repo
        self.msg_repo = msg_repo

    def create_session(
        self,
        model: str = "",
        title: str = "New Chat",
        system_prompt: str = "",
    ) -> Conversation:
        """Create a new conversation.

        Args:
            model: Ollama model name to use.
            title: Initial title (can be auto-generated later).
            system_prompt: Optional system prompt.

        Returns:
            The newly created Conversation.
        """
        conversation = self.conv_repo.create(
            model=model,
            title=title,
            system_prompt=system_prompt,
        )
        logger.info("Created session %d: '%s'", conversation.id, conversation.title)
        return conversation

    def get_sessions(self) -> List[Conversation]:
        """Get all conversations ordered by recent activity.

        Returns:
            List of all Conversation objects.
        """
        return self.conv_repo.get_all()

    def get_session(self, conv_id: int) -> Optional[Conversation]:
        """Get a single conversation by ID.

        Args:
            conv_id: Conversation ID.

        Returns:
            Conversation if found, None otherwise.
        """
        return self.conv_repo.get_by_id(conv_id)

    def rename_session(self, conv_id: int, title: str) -> None:
        """Rename a conversation.

        Args:
            conv_id: Conversation ID.
            title: New title.
        """
        self.conv_repo.update_title(conv_id, title)
        logger.info("Renamed session %d to '%s'", conv_id, title)

    def delete_session(self, conv_id: int) -> None:
        """Delete a conversation and all its messages.

        Args:
            conv_id: Conversation ID.
        """
        self.conv_repo.delete(conv_id)
        logger.info("Deleted session %d", conv_id)

    def duplicate_session(self, conv_id: int, new_model: Optional[str] = None) -> Optional[Conversation]:
        """Duplicate a conversation, optionally with a different model.

        Copies all messages to a new conversation.

        Args:
            conv_id: Source conversation ID.
            new_model: If provided, use this model instead of the original.

        Returns:
            New Conversation, or None if source not found.
        """
        source = self.conv_repo.get_by_id(conv_id)
        if source is None:
            logger.warning("Source conversation %d not found", conv_id)
            return None

        # Create new conversation
        model = new_model or source.model
        new_conv = self.conv_repo.create(
            model=model,
            title=f"{source.title} (Copy)",
            system_prompt=source.system_prompt,
        )

        # Copy all messages
        messages = self.msg_repo.get_by_conv(conv_id, limit=10000, offset=0)
        for msg in messages:
            self.msg_repo.add(new_conv.id, msg.role, msg.content)

        logger.info(
            "Duplicated session %d → %d (model: %s → %s)",
            conv_id, new_conv.id, source.model, model,
        )
        return new_conv

    def auto_title(self, conv_id: int, first_message: str, max_length: int = 50) -> str:
        """Auto-generate a title from the first user message.

        Args:
            conv_id: Conversation ID.
            first_message: The first user message content.
            max_length: Maximum title length.

        Returns:
            The generated title.
        """
        cleaned = first_message.strip().replace("\n", " ")[:max_length]
        title = cleaned if cleaned else "New Chat"
        self.conv_repo.update_title(conv_id, title)
        return title
