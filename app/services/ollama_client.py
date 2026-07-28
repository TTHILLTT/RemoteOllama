"""HTTP client for Ollama server API.

Implements the official Ollama REST API with streaming support.
Uses requests (not httpx) for compatibility with python-for-android (p4a).

API reference: https://docs.ollama.com/api/
"""

import json
from typing import Any, Generator, List, Optional

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, Timeout as RequestsTimeout

from ..models.model_info import ModelInfo
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OllamaError(Exception):
    """Base exception for Ollama API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        """Initialize OllamaError.

        Args:
            message: Error description.
            status_code: HTTP status code if available.
        """
        super().__init__(message)
        self.status_code = status_code


class OllamaConnectionError(OllamaError):
    """Raised when the server is unreachable."""

    pass


class OllamaTimeoutError(OllamaError):
    """Raised when a request times out."""

    pass


class OllamaClient:
    """HTTP client wrapper for the Ollama REST API.

    Handles all communication with the Ollama server including:
    - Model listing (GET /api/tags)
    - Chat completions with streaming (POST /api/chat)
    - Health checks (GET /)
    - Server version (GET /api/version)
    - Model details (POST /api/show)

    Uses requests.Session for connection pooling. Compatible with
    both desktop (Windows/Linux) and Android (via p4a).

    Attributes:
        base_url: Ollama server base URL.
        timeout: Request timeout in seconds.
        _session: requests Session instance (lazy-initialized).
    """

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 60) -> None:
        """Initialize OllamaClient.

        Args:
            base_url: Ollama server base URL (without trailing slash).
            timeout: HTTP request timeout in seconds.
        """
        self.base_url: str = base_url.rstrip("/")
        self.timeout: int = timeout
        self._session: Optional[requests.Session] = None
        self._current_response: Optional[requests.Response] = None

    @property
    def session(self) -> requests.Session:
        """Get or create a requests Session with connection pooling.

        Returns:
            Configured requests.Session instance.
        """
        if self._session is None:
            self._session = requests.Session()
            # Connection pool settings
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=5,
                pool_maxsize=10,
                max_retries=0,  # We handle retries ourselves
            )
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
        return self._session

    def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[dict] = None,
        stream: bool = False,
    ) -> requests.Response:
        """Make an HTTP request to the Ollama server.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API path (e.g., '/api/tags').
            json_data: Optional JSON body.
            stream: Whether to stream the response.

        Returns:
            requests Response object.

        Raises:
            OllamaConnectionError: Server unreachable.
            OllamaTimeoutError: Request timed out.
            OllamaError: Other API errors.
        """
        url = f"{self.base_url}{path}"
        logger.debug("%s %s", method, url)

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                stream=stream,
                timeout=(3.05, self.timeout),  # (connect_timeout, read_timeout)
            )

            # Store reference for cancellation (streaming mode)
            if stream:
                self._current_response = response

            # Check for HTTP errors (non-streaming mode)
            if not stream:
                self._raise_for_status(response)

            return response

        except RequestsConnectionError as e:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama server at {self.base_url}. "
                f"Is the server running?"
            ) from e
        except RequestsTimeout as e:
            raise OllamaTimeoutError(
                f"Request to {path} timed out after {self.timeout}s"
            ) from e
        except HTTPError as e:
            status_code = e.response.status_code if e.response is not None else None
            raise OllamaError(
                f"API error: {e}",
                status_code=status_code,
            ) from e

    def _raise_for_status(self, response: requests.Response) -> None:
        """Check response status and raise on error.

        Args:
            response: requests Response to check.

        Raises:
            OllamaError: On HTTP error status.
        """
        if response.status_code >= 400:
            try:
                detail = response.json().get("error", response.text)
            except (json.JSONDecodeError, AttributeError, ValueError):
                detail = response.text
            raise OllamaError(
                f"API error ({response.status_code}): {detail}",
                status_code=response.status_code,
            )

    # ── Public API Methods ──────────────────────────────────────────

    def list_models(self) -> List[ModelInfo]:
        """List all available models on the server.

        Calls GET /api/tags.

        Returns:
            List of ModelInfo objects representing available models.

        Raises:
            OllamaError: On API or connection failure.
        """
        logger.info("Fetching model list from %s/api/tags", self.base_url)
        response = self._request("GET", "/api/tags")
        data = response.json()
        models = [ModelInfo.from_api(m) for m in data.get("models", [])]
        logger.info("Found %d models", len(models))
        return models

    def chat(
        self,
        model: str,
        messages: List[dict],
        stream: bool = True,
        options: Optional[dict] = None,
    ) -> Generator[dict, None, None]:
        """Send a chat request to Ollama.

        Calls POST /api/chat. When stream=True, yields each chunk
        as a dict for incremental UI updates.

        Args:
            model: Model name (e.g., 'qwen3:14b').
            messages: List of message dicts with 'role' and 'content'.
            stream: Whether to stream the response.
            options: Optional model parameters (temperature, num_predict, etc.).

        Yields:
            Dict for each chunk (streaming) or a single dict (non-streaming).

        Raises:
            OllamaError: On API or connection failure.
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if options:
            payload["options"] = options

        logger.info(
            "Chat request: model=%s, messages=%d, stream=%s",
            model, len(messages), stream,
        )

        if stream:
            response = self._request("POST", "/api/chat", json_data=payload, stream=True)
            try:
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        try:
                            chunk = json.loads(line)
                            yield chunk
                            if chunk.get("done"):
                                total = chunk.get("total_duration", 0)
                                logger.info("Chat complete: %dms", total / 1_000_000)
                                break
                        except json.JSONDecodeError as e:
                            logger.warning("Failed to parse chunk: %s", e)
                            continue
            finally:
                response.close()
                self._current_response = None
        else:
            response = self._request("POST", "/api/chat", json_data=payload)
            data = response.json()
            yield data

    def generate(
        self,
        model: str,
        prompt: str,
        options: Optional[dict] = None,
    ) -> str:
        """Send a single generate request (non-streaming).

        Calls POST /api/generate for simple text completion.

        Args:
            model: Model name.
            prompt: The prompt text.
            options: Optional model parameters.

        Returns:
            Generated text response.

        Raises:
            OllamaError: On API or connection failure.
        """
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if options:
            payload["options"] = options

        logger.info("Generate request: model=%s", model)
        response = self._request("POST", "/api/generate", json_data=payload)
        data = response.json()
        return data.get("response", "")

    def stop(self) -> None:
        """Cancel the current streaming request.

        Closes the underlying HTTP connection to stop generation.
        """
        if self._current_response is not None:
            logger.info("Stopping current generation")
            try:
                self._current_response.close()
            except Exception as e:
                logger.warning("Error stopping request: %s", e)
            finally:
                self._current_response = None

    def health(self) -> bool:
        """Check if the Ollama server is reachable.

        Calls GET / (root endpoint).

        Returns:
            True if server responds, False otherwise.
        """
        try:
            response = self._request("GET", "/")
            return response.status_code == 200
        except OllamaError:
            return False

    def version(self) -> str:
        """Get the Ollama server version.

        Calls GET /api/version.

        Returns:
            Version string (e.g., '0.3.0').

        Raises:
            OllamaError: On API or connection failure.
        """
        response = self._request("GET", "/api/version")
        data = response.json()
        return data.get("version", "unknown")

    def show(self, model: str) -> dict:
        """Get detailed information about a model.

        Calls POST /api/show.

        Args:
            model: Model name.

        Returns:
            Dict with model details (modelfile, parameters, template, etc.).

        Raises:
            OllamaError: On API or connection failure.
        """
        response = self._request("POST", "/api/show", json_data={"name": model})
        return response.json()

    def close(self) -> None:
        """Close the underlying HTTP session and release connections."""
        if self._session is not None:
            self._session.close()
            self._session = None
            logger.debug("HTTP session closed")
