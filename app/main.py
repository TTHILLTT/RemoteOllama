"""RemoteOllama - Cross-platform AI Chat Client for Ollama.

Entry point for the application. Creates the Qt application,
initializes all services and viewmodels, and launches the QML UI.

Usage:
    python -m app.main
    python app/main.py
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

from .ui.app_window import AppWindow
from .utils.logger import setup_logging

# Ensure the app package directory is in the path for resource loading
_APP_DIR = Path(__file__).parent


def main() -> int:
    """Application entry point.

    Returns:
        Exit code (0 = success, 1 = error).
    """
    # ── Setup logging ───────────────────────────────────────────
    setup_logging()

    # ── High-DPI support ────────────────────────────────────────
    # Enable automatic scaling for high-DPI displays
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # ── Create Qt Application ───────────────────────────────────
    app = QGuiApplication(sys.argv)
    app.setApplicationName("RemoteOllama")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("RemoteOllama")

    # Set default font
    font = app.font()
    font.setPointSize(14)
    app.setFont(font)

    # ── Initialize Application ──────────────────────────────────
    try:
        window = AppWindow()
        window.initialize(app)

        # Register cleanup
        app.aboutToQuit.connect(window.cleanup)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nFATAL ERROR: {e}\n", file=sys.stderr)
        print("Please check that:", file=sys.stderr)
        print("  1. PySide6 is installed: pip install PySide6", file=sys.stderr)
        print("  2. All dependencies are installed: pip install -r requirements.txt", file=sys.stderr)
        return 1

    # ── Run event loop ──────────────────────────────────────────
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
