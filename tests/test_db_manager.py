"""Unit tests for DatabaseManager and repositories.

Uses an in-memory SQLite database for fast, isolated testing.
"""

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from app.database.conversation_repo import ConversationRepo
from app.database.db_manager import DatabaseManager
from app.database.message_repo import MessageRepo


class TestDatabaseManager:
    """Tests for DatabaseManager connection and migration."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield Path(path)
        # Cleanup
        try:
            os.unlink(path)
            os.unlink(path + "-wal")
            os.unlink(path + "-shm")
        except OSError:
            pass

    @pytest.fixture
    def db(self, temp_db_path):
        """Create a DatabaseManager with temp file."""
        manager = DatabaseManager(db_path=temp_db_path)
        manager.migrate()
        yield manager
        manager.close()

    def test_connection_created(self, db):
        """Test that get_connection returns a working connection."""
        conn = db.get_connection()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)

    def test_migration_creates_tables(self, db):
        """Test that migration creates all expected tables."""
        conn = db.get_connection()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "conversation" in table_names
        assert "message" in table_names
        assert "config" in table_names
        assert "schema_version" in table_names

    def test_migration_idempotent(self, db):
        """Test that running migration twice is safe."""
        db.migrate()  # Second call should not error
        conn = db.get_connection()
        version = conn.execute("SELECT version FROM schema_version").fetchone()
        assert version[0] == 1

    def test_wal_mode(self, db):
        """Test that WAL mode is enabled."""
        conn = db.get_connection()
        row = conn.execute("PRAGMA journal_mode").fetchone()
        assert row[0].upper() == "WAL"

    def test_foreign_keys_enabled(self, db):
        """Test that foreign keys are enforced."""
        conn = db.get_connection()
        row = conn.execute("PRAGMA foreign_keys").fetchone()
        assert row[0] == 1


class TestConversationRepo:
    """Tests for Conversation repository CRUD operations."""

    @pytest.fixture
    def db(self):
        """Create DatabaseManager with in-memory DB."""
        manager = DatabaseManager(db_path=Path(":memory:"))
        manager.migrate()
        return manager

    @pytest.fixture
    def repo(self, db):
        """Create ConversationRepo."""
        return ConversationRepo(db)

    def test_create(self, repo):
        """Test creating a conversation."""
        conv = repo.create(model="qwen3:14b", title="Test Chat")
        assert conv.id > 0
        assert conv.title == "Test Chat"
        assert conv.model == "qwen3:14b"

    def test_get_all(self, repo):
        """Test retrieving all conversations."""
        repo.create(model="qwen3", title="Chat 1")
        repo.create(model="llama3", title="Chat 2")
        all_convs = repo.get_all()
        assert len(all_convs) == 2

    def test_get_by_id(self, repo):
        """Test retrieving a conversation by ID."""
        created = repo.create(model="qwen3", title="Find Me")
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.title == "Find Me"

    def test_get_by_id_not_found(self, repo):
        """Test retrieving a non-existent conversation."""
        found = repo.get_by_id(99999)
        assert found is None

    def test_update_title(self, repo):
        """Test updating conversation title."""
        conv = repo.create(model="qwen3", title="Old Title")
        repo.update_title(conv.id, "New Title")
        updated = repo.get_by_id(conv.id)
        assert updated.title == "New Title"

    def test_delete(self, repo):
        """Test deleting a conversation."""
        conv = repo.create(model="qwen3", title="To Delete")
        repo.delete(conv.id)
        assert repo.get_by_id(conv.id) is None

    def test_delete_cascades_messages(self, repo, db):
        """Test that deleting a conversation also deletes its messages."""
        msg_repo = MessageRepo(db)
        conv = repo.create(model="qwen3", title="Cascade Test")
        msg_repo.add(conv.id, "user", "Hello")
        msg_repo.add(conv.id, "assistant", "Hi!")

        assert msg_repo.count(conv.id) == 2
        repo.delete(conv.id)
        assert msg_repo.count(conv.id) == 0


class TestMessageRepo:
    """Tests for Message repository CRUD operations."""

    @pytest.fixture
    def db(self):
        """Create DatabaseManager with in-memory DB."""
        manager = DatabaseManager(db_path=Path(":memory:"))
        manager.migrate()
        return manager

    @pytest.fixture
    def conv(self, db):
        """Create a test conversation."""
        repo = ConversationRepo(db)
        return repo.create(model="qwen3", title="Test")

    @pytest.fixture
    def repo(self, db):
        """Create MessageRepo."""
        return MessageRepo(db)

    def test_add_message(self, repo, conv):
        """Test adding a message."""
        msg = repo.add(conv.id, "user", "Hello world")
        assert msg.id > 0
        assert msg.role == "user"
        assert msg.content == "Hello world"

    def test_get_by_conv(self, repo, conv):
        """Test retrieving messages by conversation."""
        repo.add(conv.id, "user", "Q1")
        repo.add(conv.id, "assistant", "A1")
        repo.add(conv.id, "user", "Q2")

        messages = repo.get_by_conv(conv.id)
        assert len(messages) == 3
        assert messages[0].content == "Q1"
        assert messages[2].content == "Q2"

    def test_get_last_n(self, repo, conv):
        """Test getting last N messages."""
        for i in range(10):
            repo.add(conv.id, "user", f"Message {i}")

        recent = repo.get_last_n(conv.id, 3)
        assert len(recent) == 3
        assert recent[-1].content == "Message 9"

    def test_delete(self, repo, conv):
        """Test deleting a message."""
        msg = repo.add(conv.id, "user", "Delete me")
        repo.delete(msg.id)
        assert repo.get_by_id(msg.id) is None

    def test_invalid_role_rejected(self, repo, conv):
        """Test that invalid roles are rejected by CHECK constraint."""
        with pytest.raises(sqlite3.IntegrityError):
            repo.add(conv.id, "invalid_role", "content")

    def test_count(self, repo, conv):
        """Test counting messages."""
        repo.add(conv.id, "user", "Msg 1")
        repo.add(conv.id, "assistant", "Msg 2")
        assert repo.count(conv.id) == 2
