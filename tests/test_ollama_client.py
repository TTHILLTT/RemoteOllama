"""Unit tests for OllamaClient.

Uses httpx's mock transport to simulate server responses.
"""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.ollama_client import (
    OllamaClient,
    OllamaConnectionError,
    OllamaError,
    OllamaTimeoutError,
)


class TestOllamaClient:
    """Tests for the Ollama HTTP client."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return OllamaClient(base_url="http://test-server:11434", timeout=5)

    def test_initialization(self, client):
        """Test client initialization with default values."""
        assert client.base_url == "http://test-server:11434"
        assert client.timeout == 5

    def test_trailing_slash_removed(self):
        """Test trailing slash is stripped from base_url."""
        client = OllamaClient(base_url="http://test-server:11434/")
        assert client.base_url == "http://test-server:11434"

    @patch("httpx.Client.request")
    def test_health_check_success(self, mock_request, client):
        """Test health check when server responds OK."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        assert client.health() is True

    @patch("httpx.Client.request")
    def test_health_check_failure(self, mock_request, client):
        """Test health check when server is unreachable."""
        mock_request.side_effect = httpx.ConnectError("Connection refused")

        assert client.health() is False

    @patch("httpx.Client.request")
    def test_list_models(self, mock_request, client):
        """Test listing models from /api/tags."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "qwen3:14b",
                    "modified_at": "2024-01-15T10:30:00Z",
                    "size": 8544883829,
                    "digest": "abc123def456",
                },
                {
                    "name": "llama3:8b",
                    "modified_at": "2024-01-14T08:00:00Z",
                    "size": 4661222333,
                    "digest": "xyz789ghi012",
                },
            ]
        }
        mock_request.return_value = mock_response

        models = client.list_models()
        assert len(models) == 2
        assert models[0].name == "qwen3:14b"
        assert models[0].size == 8544883829
        assert models[0].digest == "abc123def456"

    @patch("httpx.Client.request")
    def test_list_models_empty(self, mock_request, client):
        """Test listing models when server has none."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_request.return_value = mock_response

        models = client.list_models()
        assert len(models) == 0

    @patch("httpx.Client.request")
    def test_version(self, mock_request, client):
        """Test getting server version."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "0.3.0"}
        mock_request.return_value = mock_response

        version = client.version()
        assert version == "0.3.0"

    @patch("httpx.Client.request")
    def test_connection_error(self, mock_request, client):
        """Test connection error is properly wrapped."""
        mock_request.side_effect = httpx.ConnectError("No route to host")

        with pytest.raises(OllamaConnectionError, match="Cannot connect"):
            client.list_models()

    @patch("httpx.Client.request")
    def test_timeout_error(self, mock_request, client):
        """Test timeout error is properly wrapped."""
        mock_request.side_effect = httpx.TimeoutException("Request timed out")

        with pytest.raises(OllamaTimeoutError, match="timed out"):
            client.list_models()

    @patch("httpx.Client.request")
    def test_chat_streaming(self, mock_request, client):
        """Test streaming chat response."""
        # Simulate streaming with iter_lines
        chunks = [
            '{"model":"qwen3","message":{"role":"assistant","content":"Hello"},"done":false}',
            '{"model":"qwen3","message":{"role":"assistant","content":" world"},"done":false}',
            '{"model":"qwen3","message":{"role":"assistant","content":"!"},"done":false}',
            '{"model":"qwen3","message":{"role":"assistant","content":""},"done":true,"total_duration":1000000}',
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = chunks
        mock_request.return_value = mock_response

        messages = [{"role": "user", "content": "Hi"}]
        result = list(client.chat("qwen3", messages, stream=True))

        assert len(result) == 4
        assert result[0]["message"]["content"] == "Hello"
        assert result[3]["done"] is True

    @patch("httpx.Client.request")
    def test_chat_non_streaming(self, mock_request, client):
        """Test non-streaming chat response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "qwen3",
            "message": {"role": "assistant", "content": "Hello world!"},
            "done": True,
        }
        mock_request.return_value = mock_response

        messages = [{"role": "user", "content": "Hi"}]
        result = list(client.chat("qwen3", messages, stream=False))

        assert len(result) == 1
        assert result[0]["message"]["content"] == "Hello world!"

    def test_close(self, client):
        """Test client close releases resources."""
        # Force client creation
        _ = client.client
        client.close()
        assert client._client is None


class TestModelInfo:
    """Tests for ModelInfo parsing."""

    def test_from_api_basic(self):
        """Test basic ModelInfo creation from API response."""
        from app.models.model_info import ModelInfo

        data = {
            "name": "qwen3:14b",
            "modified_at": "2024-01-15T10:30:00Z",
            "size": 8544883829,
            "digest": "abc123",
        }
        model = ModelInfo.from_api(data)
        assert model.name == "qwen3:14b"
        assert model.parameter_size == "14B"
        assert model.size_gb == pytest.approx(7.96, rel=0.1)

    def test_from_api_no_tag(self):
        """Test ModelInfo when name has no colon tag."""
        from app.models.model_info import ModelInfo

        data = {
            "name": "gemma",
            "size": 5000000000,
            "digest": "xyz789",
        }
        model = ModelInfo.from_api(data)
        assert model.name == "gemma"
        assert model.parameter_size == ""
        assert model.size_display == pytest.approx("4.7 GB", abs=0.1)
