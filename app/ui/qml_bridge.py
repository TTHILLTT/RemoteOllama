"""Python ↔ QML bridge.

Registers Python ViewModel objects as QML context properties so they
are accessible from QML files. Also registers QML types and singletons.
"""

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from ..utils.logger import get_logger

logger = get_logger(__name__)


class QMLBridge:
    """Bridges Python backend with QML frontend.

    Loads QML files, registers Python objects as context properties,
    and manages the QQmlApplicationEngine lifecycle.

    Attributes:
        engine: The QQmlApplicationEngine instance.
        _qml_dir: Directory containing QML files.
    """

    def __init__(self, qml_dir: Optional[Path] = None) -> None:
        """Initialize QMLBridge.

        Args:
            qml_dir: Path to QML resources directory. Defaults to resources/qml.
        """
        self._qml_dir = qml_dir or Path(__file__).parent.parent / "resources" / "qml"
        self.engine: Optional[QQmlApplicationEngine] = None

    def initialize(self, app: QGuiApplication) -> QQmlApplicationEngine:
        """Initialize the QML engine and register context properties.

        Args:
            app: The QGuiApplication instance.

        Returns:
            Configured QQmlApplicationEngine.
        """
        self.engine = QQmlApplicationEngine()

        # Add QML import path
        self.engine.addImportPath(str(self._qml_dir))

        logger.info("QML import path: %s", self._qml_dir)

        return self.engine

    def register_context(self, name: str, obj: QObject) -> None:
        """Register a Python QObject as a QML context property.

        The object becomes accessible in QML by its name.

        Args:
            name: Name to use in QML (e.g., 'chatVM').
            obj: The QObject to expose.
        """
        if self.engine is None:
            raise RuntimeError("QMLBridge not initialized. Call initialize() first.")
        self.engine.rootContext().setContextProperty(name, obj)
        logger.debug("Registered QML context: %s → %s", name, type(obj).__name__)

    def load_main(self, qml_file: str = "MainWindow.qml") -> None:
        """Load the main QML file.

        Args:
            qml_file: QML filename to load as main.

        Raises:
            FileNotFoundError: If QML file doesn't exist.
            RuntimeError: If QML loading fails.
        """
        if self.engine is None:
            raise RuntimeError("QMLBridge not initialized. Call initialize() first.")

        qml_path = self._qml_dir / qml_file
        if not qml_path.exists():
            raise FileNotFoundError(f"QML file not found: {qml_path}")

        url = QUrl.fromLocalFile(str(qml_path))
        self.engine.load(url)

        if not self.engine.rootObjects():
            raise RuntimeError(f"Failed to load QML file: {qml_path}")

        logger.info("Loaded QML main file: %s", qml_path)

    def get_root_object(self) -> Optional[QObject]:
        """Get the root QML object (ApplicationWindow).

        Returns:
            Root QObject or None if not loaded.
        """
        if self.engine is None:
            return None
        objects = self.engine.rootObjects()
        return objects[0] if objects else None
