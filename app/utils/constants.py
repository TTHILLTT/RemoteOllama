"""Application-wide constants."""

import os
from pathlib import Path

APP_NAME = "RemoteOllama"
APP_VERSION = "1.0.0"
APP_ORG = "RemoteOllama"

# Config file path
CONFIG_DIR = Path.home() / f".{APP_NAME.lower()}"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Database file path
DB_DIR = CONFIG_DIR / "data"
DB_FILE = DB_DIR / "remoteollama.db"

# Default Ollama server
DEFAULT_SERVER_URL = "http://localhost:11434"

# HTTP defaults
DEFAULT_TIMEOUT = 60  # seconds
MAX_RETRIES = 3

# UI constants
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
SIDEBAR_DEFAULT_WIDTH = 260
SIDEBAR_MIN_WIDTH = 200
SIDEBAR_MAX_WIDTH = 400
DEFAULT_FONT_SIZE = 14
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 48

# Chat constants
MAX_CONTEXT_MESSAGES = 50
AUTO_TITLE_MAX_LENGTH = 50
MESSAGE_PAGE_SIZE = 50  # messages per page for lazy loading

# Supported Markdown features
ENABLE_CODE_HIGHLIGHT = True
ENABLE_LATEX = True
ENABLE_TABLES = True
