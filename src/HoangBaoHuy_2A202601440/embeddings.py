from __future__ import annotations

import os
from typing import Callable

EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"
LOCAL_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"


def _mock_embed(text: str, dim: int = 64) -> list[float]:
    """Generate a deterministic pseudo-random embedding vector for testing."""
    import hashlib

    hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
    raw = [float(b) for b in hash_bytes]
    while len(raw) < dim:
        raw.extend(raw)
    raw = raw[:dim]
    norm = sum(x * x for x in raw) ** 0.5
    return [x / norm for x in raw] if norm > 0 else raw


class MockEmbedder:
    """Callable wrapper around _mock_embed."""

    _backend_name = "mock"

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    def __call__(self, text: str) -> list[float]:
        return _mock_embed(text, dim=self.dim)


class LocalEmbedder:
    """Local multilingual embeddings via sentence-transformers."""

    _backend_name = "sentence-transformers local"

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name)
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Install requirements-local.txt."
            ) from exc

    def __call__(self, text: str) -> list[float]:
        vector = self.model.encode(text, convert_to_numpy=True)
        return vector.tolist()


class OpenAIEmbedder:
    """Embeddings via OpenAI's API."""

    _backend_name = "openai"

    def __init__(self, model_name: str = OPENAI_EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        try:
            import openai

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError as exc:
            raise RuntimeError("openai package is not installed.") from exc

    def __call__(self, text: str) -> list[float]:
        response = self.client.embeddings.create(input=text, model=self.model_name)
        return response.data[0].embedding
