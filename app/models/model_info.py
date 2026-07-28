"""Model info data model (from Ollama /api/tags)."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelInfo:
    """Represents an Ollama model returned by GET /api/tags.

    Attributes:
        name: Model name (e.g., 'qwen3:14b', 'llama3:8b').
        modified_at: Last modification timestamp from server.
        size: Model size in bytes (human-readable string also available).
        digest: SHA256 digest of the model.
        parameter_size: Human-readable parameter count (e.g., '14B').
    """

    name: str = ""
    modified_at: str = ""
    size: int = 0
    digest: str = ""
    parameter_size: str = ""

    @property
    def display_name(self) -> str:
        """Human-friendly display name."""
        return self.name

    @property
    def size_gb(self) -> float:
        """Model size in gigabytes."""
        return round(self.size / (1024 ** 3), 2)

    @property
    def size_display(self) -> str:
        """Human-readable size string."""
        if self.size >= 1024 ** 3:
            return f"{self.size_gb:.1f} GB"
        if self.size >= 1024 ** 2:
            return f"{self.size / (1024 ** 2):.0f} MB"
        return f"{self.size / 1024:.0f} KB"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "modified_at": self.modified_at,
            "size": self.size,
            "digest": self.digest,
            "parameter_size": self.parameter_size,
        }

    @classmethod
    def from_api(cls, data: dict) -> "ModelInfo":
        """Create instance from /api/tags response item.

        Example API response item:
            {
                "name": "qwen3:14b",
                "modified_at": "2024-01-15T10:30:00Z",
                "size": 8544883829,
                "digest": "abc123..."
            }
        """
        name = data.get("name", "")
        # Extract parameter size from name if possible (e.g., 'qwen3:14b' → '14B')
        param_size = ""
        if ":" in name:
            tag = name.split(":")[-1]
            if tag and tag[0].isdigit():
                param_size = tag.upper()

        return cls(
            name=name,
            modified_at=data.get("modified_at", ""),
            size=data.get("size", 0),
            digest=data.get("digest", ""),
            parameter_size=param_size,
        )
