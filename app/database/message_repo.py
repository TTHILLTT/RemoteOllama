"""Repository for message CRUD operations."""

import sqlite3
from typing import List, Optional

from ..models.message import Message, MessageRole
from ..utils.logger import get_logger
from .db_manager import DatabaseManager

logger = get_logger(__name__)


class MessageRepo:
    """Data access layer for the message table.

    All methods operate within the context of a DatabaseManager,
    which provides thread-local connections.

    Attributes:
        db: DatabaseManager instance.
    """

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize MessageRepo.

        Args:
            db: DatabaseManager for connection management.
        """
        self.db = db

    def add(self, conv_id: int, role: MessageRole, content: str) -> Message:
        """Add a new message to a conversation.

        Args:
            conv_id: Parent conversation ID.
            role: Message role ('system', 'user', or 'assistant').
            content: Message content.

        Returns:
            Created Message with generated ID.

        Raises:
            sqlite3.Error: On database failure.
        """
        conn = self.db.get_connection()
        cursor = conn.execute(
            "INSERT INTO message (conversation_id, role, content) VALUES (?, ?, ?)",
            (conv_id, role, content),
        )
        # Also update the parent conversation's timestamp
        conn.execute(
            "UPDATE conversation SET updated_at = datetime('now') WHERE id = ?",
            (conv_id,),
        )
        conn.commit()
        msg = Message(
            id=cursor.lastrowid,
            conversation_id=conv_id,
            role=role,
            content=content,
        )
        logger.debug("Added %s message %d to conversation %d", role, msg.id, conv_id)
        return msg

    def get_by_conv(
        self, conv_id: int, limit: int = 50, offset: int = 0
    ) -> List[Message]:
        """Get messages for a conversation with pagination.

        Args:
            conv_id: Parent conversation ID.
            limit: Maximum messages to return.
            offset: Number of messages to skip from the start.

        Returns:
            List of Message objects, ordered by creation time ascending.
        """
        conn = self.db.get_connection()
        rows = conn.execute(
            """SELECT * FROM message
               WHERE conversation_id = ?
               ORDER BY created_at ASC
               LIMIT ? OFFSET ?""",
            (conv_id, limit, offset),
        ).fetchall()
        return [Message.from_dict(dict(row)) for row in rows]

    def get_last_n(self, conv_id: int, n: int = 50) -> List[Message]:
        """Get the most recent N messages for a conversation.

        Used for building the context array for /api/chat.

        Args:
            conv_id: Parent conversation ID.
            n: Number of recent messages to retrieve.

        Returns:
            List of up to N most recent Message objects.
        """
        conn = self.db.get_connection()
        rows = conn.execute(
            """SELECT * FROM (
                   SELECT * FROM message
                   WHERE conversation_id = ?
                   ORDER BY created_at DESC
                   LIMIT ?
               ) ORDER BY created_at ASC""",
            (conv_id, n),
        ).fetchall()
        messages = [Message.from_dict(dict(row)) for row in rows]
        return messages

    def get_by_id(self, msg_id: int) -> Optional[Message]:
        """Get a single message by ID.

        Args:
            msg_id: Message ID.

        Returns:
            Message if found, None otherwise.
        """
        conn = self.db.get_connection()
        row = conn.execute(
            "SELECT * FROM message WHERE id = ?", (msg_id,)
        ).fetchone()
        if row is None:
            return None
        return Message.from_dict(dict(row))

    def delete(self, msg_id: int) -> None:
        """Delete a single message.

        Args:
            msg_id: Message ID.
        """
        conn = self.db.get_connection()
        conn.execute("DELETE FROM message WHERE id = ?", (msg_id,))
        conn.commit()
        logger.debug("Deleted message %d", msg_id)

    def delete_from(self, conv_id: int, from_msg_id: int) -> None:
        """Delete a message and all messages after it in the conversation.

        Used for 'edit and regenerate' functionality.

        Args:
            conv_id: Parent conversation ID.
            from_msg_id: Delete this message and all later messages.
        """
        conn = self.db.get_connection()
        # Get the timestamp of the target message
        row = conn.execute(
            "SELECT created_at FROM message WHERE id = ?", (from_msg_id,)
        ).fetchone()
        if row is None:
            logger.warning("Message %d not found for delete_from", from_msg_id)
            return

        conn.execute(
            """DELETE FROM message
               WHERE conversation_id = ?
                 AND created_at >= ?""",
            (conv_id, row["created_at"]),
        )
        conn.commit()
        logger.debug("Deleted messages from %d onward in conversation %d", from_msg_id, conv_id)

    def update_content(self, msg_id: int, content: str) -> None:
        """Update the content of an existing message.

        Args:
            msg_id: Message ID.
            content: New content.
        """
        conn = self.db.get_connection()
        conn.execute(
            "UPDATE message SET content = ? WHERE id = ?",
            (content, msg_id),
        )
        conn.commit()
        logger.debug("Updated message %d content", msg_id)

    def count(self, conv_id: int) -> int:
        """Count messages in a conversation.

        Args:
            conv_id: Conversation ID.

        Returns:
            Number of messages.
        """
        conn = self.db.get_connection()
        row = conn.execute(
            "SELECT COUNT(*) FROM message WHERE conversation_id = ?", (conv_id,)
        ).fetchone()
        return row[0] if row else 0

    def get_all_as_api_messages(self, conv_id: int, max_messages: int = 50) -> List[dict]:
        """Get messages formatted for Ollama /api/chat.

        Returns the most recent messages in the format expected by the API,
        including the system prompt if one exists.

        Args:
            conv_id: Parent conversation ID.
            max_messages: Maximum number of messages to include.

        Returns:
            List of dicts with 'role' and 'content' keys.
        """
        messages = self.get_last_n(conv_id, max_messages)
        return [msg.to_api_format() for msg in messages]
