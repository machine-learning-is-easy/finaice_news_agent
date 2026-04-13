"""
Text embedding service.
Supports OpenAI embeddings (default) or a local sentence-transformers model.
"""
from typing import Optional
import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class Embedder:
    def __init__(self):
        self.provider = settings.embedding_provider
        self.model = settings.embedding_model
        self.dim = settings.embedding_dim
        self._client = None

    def _get_openai_client(self):
        if self._client is None:
            import openai
            self._client = openai.OpenAI(api_key=settings.openai_api_key)
        return self._client

    def embed_text(self, text: str) -> list[float]:
        text = text[:8000]  # hard cap to stay within token limits

        if self.provider == "openai":
            return self._embed_openai(text)
        return self._embed_local(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self.provider == "openai":
            client = self._get_openai_client()
            texts = [t[:8000] for t in texts]
            response = client.embeddings.create(input=texts, model=self.model)
            return [item.embedding for item in response.data]
        return [self._embed_local(t) for t in texts]

    def _embed_openai(self, text: str) -> list[float]:
        client = self._get_openai_client()
        response = client.embeddings.create(input=[text], model=self.model)
        return response.data[0].embedding

    def _embed_local(self, text: str) -> list[float]:
        """
        Fallback: returns a zero vector.
        Replace with sentence-transformers for a real local model.
        """
        logger.warning("embedder.local_fallback_used")
        return [0.0] * self.dim
