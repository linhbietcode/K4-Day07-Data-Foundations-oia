from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """A document or text chunk with content and metadata."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
