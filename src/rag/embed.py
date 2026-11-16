"""Embeddings.

Production: bge-small-zh-v1.5 (512-d, Chinese/multilingual, CPU-friendly).
The hashing embedder is a fallback for offline/no-model environments; same interface.
To swap models, implement `dim` + `embed()` and return it from `build_embedder()`.
Changing the dimension requires rebuilding the index.
"""

from __future__ import annotations

import hashlib
import re
from typing import Protocol, Sequence

import numpy as np

_TOKEN_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]")


class Embedder(Protocol):
    dim: int

    def embed(self, texts: Sequence[str]) -> np.ndarray: ...


def _tokens(text: str) -> list[str]:
    words = _TOKEN_RE.findall(text.lower())
    bigrams = [f"{a}~{b}" for a, b in zip(words, words[1:])]
    return words + bigrams


def _hash64(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big")


class HashingEmbedder:
    """Feature hashing with signed buckets. No deps, deterministic; fallback only."""

    def __init__(self, dim: int = 256) -> None:
        if dim <= 0:
            raise ValueError("dim must be > 0")
        self.dim = dim

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in _tokens(text):
                h = _hash64(token)
                sign = 1.0 if (h >> 63) & 1 else -1.0
                out[row, h % self.dim] += sign
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        np.divide(out, norms, out=out, where=norms > 0)
        return out


class SentenceTransformerEmbedder:
    """bge-small-zh-v1.5: Chinese/multilingual retrieval, L2-normalized output."""

    def __init__(self, name: str = "BAAI/bge-small-zh-v1.5") -> None:
        from sentence_transformers import SentenceTransformer  # lazy import

        self._model = SentenceTransformer(name)
        self.dim = int(self._model.get_embedding_dimension())

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        vecs = self._model.encode(
            list(texts), normalize_embeddings=True, show_progress_bar=False
        )
        return np.asarray(vecs, dtype=np.float32)


def build_embedder(dim: int = 512) -> Embedder:
    """Prefer the real model; fall back to hashing if it cannot load."""
    try:
        return SentenceTransformerEmbedder("BAAI/bge-small-zh-v1.5")
    except Exception as exc:  # noqa: BLE001
        print(f"[embed] real embedder unavailable, falling back to hashing: {exc}")
        return HashingEmbedder(dim)
