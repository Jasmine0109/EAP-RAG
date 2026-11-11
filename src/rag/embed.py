"""向量化。

默认实现是「特征哈希」嵌入：无模型、无网络、确定性，用来先把整条链路跑通。
它的语义检索能力很弱（本质是词面重合），**换真模型是第一步升级**。

替换方法：实现同样的 `dim` + `embed()` 接口，在 `build_embedder()` 里返回即可。
注意换维度后旧索引要重建（`rag reset`）。
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
    # 中文单字信息量低，补一层相邻二元组，让短语也能命中
    bigrams = [f"{a}~{b}" for a, b in zip(words, words[1:])]
    return words + bigrams


def _hash64(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big")


class HashingEmbedder:
    """特征哈希 + 带符号散列。确定性依赖 blake2b，跨进程、跨机器稳定。"""

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


def build_embedder(dim: int = 256) -> Embedder:
    """工厂：以后换成真模型只改这里。"""
    return HashingEmbedder(dim)
