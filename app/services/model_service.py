"""Model management service.

Handles fetching, caching, and refreshing the model list from Ollama server.
"""

from typing import List, Optional

from ..models.model_info import ModelInfo
from ..utils.logger import get_logger
from .ollama_client import OllamaClient, OllamaError

logger = get_logger(__name__)


class ModelService:
    """Manages available Ollama models.

    Fetches models from the server and maintains an in-memory cache.
    Models are identified by name (from /api/tags).

    Attributes:
        client: Ollama HTTP client.
        _models_cache: In-memory cache of ModelInfo objects.
        _last_fetch_time: Track when models were last fetched.
    """

    def __init__(self, client: OllamaClient) -> None:
        """Initialize ModelService.

        Args:
            client: Ollama API client for fetching models.
        """
        self.client = client
        self._models_cache: List[ModelInfo] = []

    def fetch_models(self, force: bool = False) -> List[ModelInfo]:
        """Fetch available models from the Ollama server.

        Results are cached in memory. Use force=True to bypass cache.

        Args:
            force: If True, always fetch from server even if cached.

        Returns:
            List of available ModelInfo objects.

        Raises:
            OllamaError: On connection or API failure.
        """
        if not force and self._models_cache:
            logger.debug("Returning %d cached models", len(self._models_cache))
            return self._models_cache

        logger.info("Fetching models from server...")
        try:
            self._models_cache = self.client.list_models()
            logger.info("Fetched %d models", len(self._models_cache))
            return self._models_cache
        except OllamaError:
            logger.exception("Failed to fetch models")
            raise

    def get_cached_models(self) -> List[ModelInfo]:
        """Get models from cache without fetching.

        Returns:
            List of cached ModelInfo objects (may be empty).
        """
        return list(self._models_cache)

    def get_model_by_name(self, name: str) -> Optional[ModelInfo]:
        """Find a model by exact name match.

        Args:
            name: Model name to find.

        Returns:
            ModelInfo if found, None otherwise.
        """
        for model in self._models_cache:
            if model.name == name:
                return model
        return None

    def get_model_names(self) -> List[str]:
        """Get just the model names (for display in selectors).

        Returns:
            List of model name strings.
        """
        return [m.name for m in self._models_cache]

    def refresh_models(self) -> List[ModelInfo]:
        """Force-refresh the model list from the server.

        Returns:
            Updated list of ModelInfo objects.

        Raises:
            OllamaError: On connection or API failure.
        """
        return self.fetch_models(force=True)

    def has_models(self) -> bool:
        """Check if any models are available (cached or fetched).

        Returns:
            True if at least one model is cached.
        """
        return len(self._models_cache) > 0
