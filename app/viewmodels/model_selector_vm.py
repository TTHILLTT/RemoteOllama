"""ViewModel for the model selector dialog.

Manages the list of available models from the Ollama server.
"""

from typing import List, Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

from ..services.model_service import ModelService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ModelSelectorVM(QObject):
    """ViewModel for model selection UI.

    Exposes the list of available models and the currently selected model
    as Qt properties for QML binding.

    Signals:
        models_changed: Model list updated.
        selected_model_changed: Selected model name changed.
        loading_changed: Loading state changed.
    """

    models_changed = Signal()
    selected_model_changed = Signal()
    loading_changed = Signal()

    def __init__(self, model_service: ModelService, parent: Optional[QObject] = None) -> None:
        """Initialize ModelSelectorVM.

        Args:
            model_service: Model management service.
            parent: Qt parent.
        """
        super().__init__(parent)
        self._service = model_service
        self._selected_model: str = ""
        self._loading: bool = False

    # ── Properties ──────────────────────────────────────────────

    def _get_models(self) -> list:
        """Get models as list of dicts for QML display."""
        return [m.to_dict() for m in self._service.get_cached_models()]

    models = Property("QVariantList", _get_models, notify=models_changed)

    def _get_model_names(self) -> list:
        """Get just model names for simple selectors."""
        return self._service.get_model_names()

    model_names = Property("QVariantList", _get_model_names, notify=models_changed)

    def _get_selected(self) -> str:
        return self._selected_model

    def _set_selected(self, name: str) -> None:
        if self._selected_model != name:
            self._selected_model = name
            self.selected_model_changed.emit()
            logger.debug("Selected model: %s", name)

    selected_model = Property(str, _get_selected, _set_selected, notify=selected_model_changed)

    def _get_loading(self) -> bool:
        return self._loading

    loading = Property(bool, _get_loading, notify=loading_changed)

    # ── Slots ───────────────────────────────────────────────────

    @Slot()
    def fetch_models(self) -> None:
        """Fetch models from the server."""
        if self._loading:
            return

        self._loading = True
        self.loading_changed.emit()

        try:
            models = self._service.fetch_models(force=True)
            self.models_changed.emit()
            logger.info("Fetched %d models", len(models))
        except Exception as e:
            logger.exception("Failed to fetch models: %s", e)
        finally:
            self._loading = False
            self.loading_changed.emit()

    @Slot(str)
    def select_model(self, name: str) -> None:
        """Select a model by name.

        Args:
            name: Model name to select.
        """
        self._set_selected(name)

    @Slot(str, result="QVariant")
    def get_model_info(self, name: str) -> dict:
        """Get detailed info for a model.

        Args:
            name: Model name.

        Returns:
            Model info dict, or empty dict.
        """
        model = self._service.get_model_by_name(name)
        return model.to_dict() if model else {}
