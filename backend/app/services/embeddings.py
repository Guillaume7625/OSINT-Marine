from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

# Sentence Transformers runs on PyTorch for this project; disable TensorFlow import paths.
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

from app.core.config import Settings


class EmbeddingModel(Protocol):
    dimension: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding per input text."""


@dataclass(slots=True)
class SentenceTransformerEmbeddingModel:
    model_name: str
    dimension: int
    batch_size: int = 32
    _model: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError(
                "sentence-transformers is required for EMBEDDING_BACKEND=sentence-transformers"
            ) from exc

        self._model = SentenceTransformer(self.model_name)
        model_dimension = self._model.get_sentence_embedding_dimension()
        if model_dimension is None:
            raise RuntimeError("Embedding model did not expose embedding dimension")
        if model_dimension != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: model={model_dimension} config={self.dimension}. "
                "Update EMBEDDING_DIMENSION or choose a compatible embedding model."
            )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        arr = np.asarray(vectors, dtype=np.float32)
        return arr.tolist()


class DeterministicTestEmbeddingModel:
    """Test-only deterministic embedding model."""

    def __init__(self, dimension: int = 8):
        self.dimension = dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        output: list[list[float]] = []
        for text in texts:
            vec = np.zeros(self.dimension, dtype=np.float32)
            for token in text.lower().split():
                idx = abs(hash(token)) % self.dimension
                vec[idx] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            output.append(vec.tolist())
        return output


def build_embedding_model(settings: Settings) -> EmbeddingModel:
    if settings.embedding_backend == "sentence-transformers":
        return SentenceTransformerEmbeddingModel(
            model_name=settings.embedding_model_name,
            dimension=settings.embedding_dimension,
            batch_size=settings.embedding_batch_size,
        )

    raise ValueError(f"Unsupported embedding backend: {settings.embedding_backend}")
