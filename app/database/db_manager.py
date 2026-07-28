"""SQLite database connection manager with schema migration.

Provides singleton-like connection management, automatic migration,
and WAL mode for concurrent read/write performance.
"""

import sqlite3
import threading
from pathlib import Path
from typing import Optional

from ..utils.constants import DB_FILE, DB_DIR
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Schema version for future migrations
SCHEMA_VERSION = 1

CREATE_TABLES_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

-- Conversations (chat sessions)
CREATE TABLE IF NOT EXISTS conversation (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT    NOT NULL DEFAULT 'New Chat',
    model         TEXT    NOT NULL DEFAULT '',
    system_prompt TEXT    DEFAULT '',
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Messages within a conversation
CREATE TABLE IF NOT EXISTS message (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role            TEXT    NOT NULL CHECK(role IN ('system', 'user', 'assistant')),
    content         TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversation(id) ON DELETE CASCADE
);

-- Key-value configuration store
CREATE TABLE IF NOT EXISTS config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_message_conv ON message(conversation_id);
CREATE INDEX IF NOT EXISTS idx_message_time ON message(created_at);
CREATE INDEX IF NOT EXISTS idx_conversation_updated ON conversation(updated_at DESC);
"""


class DatabaseManager:
    """Manages SQLite database connection and schema.

    Uses check_same_thread=False with thread-local connections for safety.
    WAL mode is enabled for better concurrent read performance.

    Attributes:
        db_path: Path to the SQLite database file.
        _local: Thread-local storage for connections.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize DatabaseManager.

        Args:
            db_path: Path to SQLite file. Uses default if not provided.
        """
        self.db_path: Path = db_path or DB_FILE
        self._local = threading.local()
        logger.info("DatabaseManager initialized: %s", self.db_path)

    def get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection.

        Creates a new connection for the current thread if one doesn't exist.
        Connections use WAL mode and return Row objects for dict-like access.

        Returns:
            sqlite3.Connection configured for this thread.
        """
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=10.0,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=5000")
            self._local.connection = conn
            logger.debug("New database connection created for thread %s", threading.get_ident())
        return self._local.connection

    def migrate(self) -> None:
        """Run database migrations.

        Creates tables if they don't exist. Future migrations will be
        version-gated based on schema_version table.
        """
        conn = self.get_connection()
        try:
            current_version = self._get_schema_version(conn)

            if current_version == 0:
                logger.info("Running initial schema migration...")
                conn.executescript(CREATE_TABLES_SQL)
                conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
                conn.commit()
                logger.info("Schema migrated to version %d", SCHEMA_VERSION)
            elif current_version < SCHEMA_VERSION:
                self._run_migrations(conn, current_version)
            else:
                logger.debug("Schema is up to date (v%d)", current_version)
        except sqlite3.Error as e:
            logger.error("Migration failed: %s", e)
            conn.rollback()
            raise

    def _get_schema_version(self, conn: sqlite3.Connection) -> int:
        """Get current schema version from database.

        Args:
            conn: Active database connection.

        Returns:
            Current schema version, or 0 if no version table exists.
        """
        try:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            ).fetchone()
            if row is None:
                return 0
            version_row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
            return version_row[0] if version_row and version_row[0] else 0
        except sqlite3.Error:
            return 0

    def _run_migrations(self, conn: sqlite3.Connection, from_version: int) -> None:
        """Run incremental migrations from a given version.

        Args:
            conn: Active database connection.
            from_version: Current schema version to migrate from.
        """
        # Future migrations go here:
        # if from_version < 2:
        #     conn.execute("ALTER TABLE ...")
        #     conn.execute("UPDATE schema_version SET version = 2")
        logger.info("No incremental migrations needed (v%d → v%d)", from_version, SCHEMA_VERSION)

    def close(self) -> None:
        """Close the thread-local connection if open."""
        if hasattr(self._local, "connection") and self._local.connection:
            try:
                self._local.connection.close()
            except sqlite3.Error as e:
                logger.warning("Error closing connection: %s", e)
            finally:
                self._local.connection = None
                logger.debug("Database connection closed for thread %s", threading.get_ident())

    def close_all(self) -> None:
        """Close connection on the current thread (alias for close)."""
        self.close()
