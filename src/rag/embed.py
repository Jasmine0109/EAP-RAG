"""向量化。

生产用 bge-small-zh-v1.5（中文检索，512 维，CPU 可跑）；
哈希嵌入只作无网络/无模型时的兜底，接口一致（dim + embed）。
换模型：实现同样的接口，在 build_embedder() 里返回即可。
注意：换维度后旧索引要重建（索引文件可删，语料在 corpus/processed 可重跑）。
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
    """特征哈希 + 带符号散列。无依赖、确定性，仅作兜底。"""

    def __init__(self, dim: int = 256) -> None:
        if dim <= 0:
            raise ValueError("dim 必须大于 0")
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
    """bge-small-zh-v1.5：中文语义检索，输出 L2 归一向量。"""

    def __init__(self, name: str = "BAAI/bge-small-zh-v1.5") -> None:
        from sentence_transformers import SentenceTransformer  # 延迟导入，避免无模型时崩

        self._model = SentenceTransformer(name)
        self.dim = int(self._model.get_embedding_dimension())

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        vecs = self._model.encode(
            list(texts), normalize_embeddings=True, show_progress_bar=False
        )
        return np.asarray(vecs, dtype=np.float32)


def build_embedder(dim: int = 512) -> Embedder:
    """优先用真嵌入模型；加载失败则退回哈希嵌入（会明显变弱，仅保链路可跑）。"""
    try:
        return SentenceTransformerEmbedder("BAAI/bge-small-zh-v1.5")
    except Exception as exc:  # noqa: BLE001
        print(f"[embed] 真嵌入模型不可用，退回哈希嵌入：{exc}")
        return HashingEmbedder(dim)
