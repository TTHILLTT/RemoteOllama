"""Repository for conversation CRUD operations."""

import sqlite3
from typing import List, Optional

from ..models.conversation import Conversation
from ..utils.logger import get_logger
from .db_manager import DatabaseManager

logger = get_logger(__name__)


class ConversationRepo:
    """Data access layer for the conversation table.

    All methods operate within the context of a DatabaseManager,
    which provides thread-local connections.

    Attributes:
        db: DatabaseManager instance.
    """

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize ConversationRepo.

        Args:
            db: DatabaseManager for connection management.
        """
        self.db = db

    def create(self, model: str = "", title: str = "New Chat", system_prompt: str = "") -> Conversation:
        """Create a new conversation.

        Args:
            model: Ollama model name.
            title: Conversation title.
            system_prompt: Optional system prompt.

        Returns:
            Created Conversation with generated ID.

        Raises:
            sqlite3.Error: On database failure.
        """
        conn = self.db.get_connection()
        cursor = conn.execute(
            """INSERT INTO conversation (title, model, system_prompt)
               VALUES (?, ?, ?)""",
            (title, model, system_prompt),
        )
        conn.commit()
        conv = Conversation(
            id=cursor.lastrowid,
            title=title,
            model=model,
            system_prompt=system_prompt,
        )
        logger.info("Created conversation %d: '%s' with model '%s'", conv.id, conv.title, conv.model)
        return conv

    def get_all(self) -> List[Conversation]:
        """Get all conversations, ordered by most recently updated.

        Returns:
            List of all Conversation objects.
        """
        conn = self.db.get_connection()
        rows = conn.execute(
            "SELECT * FROM conversation ORDER BY updated_at DESC"
        ).fetchall()
        return [Conversation.from_dict(dict(row)) for row in rows]

    def get_by_id(self, conv_id: int) -> Optional[Conversation]:
        """Get a single conversation by ID.

        Args:
            conv_id: Conversation ID.

        Returns:
            Conversation if found, None otherwise.
        """
        conn = self.db.get_connection()
        row = conn.execute(
            "SELECT * FROM conversation WHERE id = ?", (conv_id,)
        ).fetchone()
        if row is None:
            return None
        return Conversation.from_dict(dict(row))

    def update_title(self, conv_id: int, title: str) -> None:
        """Update conversation title.

        Args:
            conv_id: Conversation ID.
            title: New title.
        """
        conn = self.db.get_connection()
        conn.execute(
            "UPDATE conversation SET title = ?, updated_at = datetime('now') WHERE id = ?",
            (title, conv_id),
        )
        conn.commit()
        logger.debug("Updated conversation %d title to '%s'", conv_id, title)

    def update_model(self, conv_id: int, model: str) -> None:
        """Update the model for a conversation.

        Args:
            conv_id: Conversation ID.
            model: New model name.
        """
        conn = self.db.get_connection()
        conn.execute(
            "UPDATE conversation SET model = ?, updated_at = datetime('now') WHERE id = ?",
            (model, conv_id),
        )
        conn.commit()
        logger.debug("Updated conversation %d model to '%s'", conv_id, model)

    def touch(self, conv_id: int) -> None:
        """Update the updated_at timestamp without changing other fields.

        Args:
            conv_id: Conversation ID.
        """
        conn = self.db.get_connection()
        conn.execute(
            "UPDATE conversation SET updated_at = datetime('now') WHERE id = ?",
            (conv_id,),
        )
        conn.commit()

    def delete(self, conv_id: int) -> None:
        """Delete a conversation and all its messages (CASCADE).

        Args:
            conv_id: Conversation ID.
        """
        conn = self.db.get_connection()
        conn.execute("DELETE FROM conversation WHERE id = ?", (conv_id,))
        conn.commit()
        logger.info("Deleted conversation %d", conv_id)

    def get_total_count(self) -> int:
        """Get total number of conversations.

        Returns:
            Count of all conversations.
        """
        conn = self.db.get_connection()
        row = conn.execute("SELECT COUNT(*) FROM conversation").fetchone()
        return row[0] if row else 0
