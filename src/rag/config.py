"""集中配置：环境变量覆盖默认值。

所有路径默认相对仓库根目录解析，整个目录搬走也不用改配置。
没有配置文件格式 —— 这个骨架阶段，环境变量足够，少一层抽象。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# src/rag/config.py -> src/rag -> src -> 仓库根
ROOT = Path(__file__).resolve().parents[2]


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def _str(name: str, default: str) -> str:
    raw = os.getenv(name)
    return default if raw is None or raw == "" else raw


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Config:
    """一次运行需要的全部参数。不可变，方便传给子模块。"""

    data_dir: Path
    index_path: Path
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 5
    embed_dim: int = 256
    llm_base_url: str = "http://127.0.0.1:8000/v1"
    llm_model: str = "qwen3.8-27b-local"
    llm_api_key: str = "sk-local"
    llm_timeout: int = 120
    offline: bool = False

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size 必须大于 0")
        if not 0 <= self.chunk_overlap < self.chunk_size:
            raise ValueError("chunk_overlap 必须满足 0 <= overlap < chunk_size")
        if self.top_k <= 0:
            raise ValueError("top_k 必须大于 0")
        if self.embed_dim <= 0:
            raise ValueError("embed_dim 必须大于 0")


def load() -> Config:
    """从环境变量构造配置。"""
    data_dir = Path(_str("RAG_DATA_DIR", str(ROOT / "data"))).expanduser()
    return Config(
        data_dir=data_dir,
        index_path=Path(_str("RAG_INDEX_PATH", str(data_dir / "index" / "index.sqlite3"))).expanduser(),
        chunk_size=_int("RAG_CHUNK_SIZE", 800),
        chunk_overlap=_int("RAG_CHUNK_OVERLAP", 120),
        top_k=_int("RAG_TOP_K", 5),
        embed_dim=_int("RAG_EMBED_DIM", 256),
        llm_base_url=_str("RAG_LLM_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/"),
        llm_model=_str("RAG_LLM_MODEL", "qwen3.8-27b-local"),
        llm_api_key=_str("RAG_LLM_API_KEY", "sk-local"),
        llm_timeout=_int("RAG_LLM_TIMEOUT", 120),
        offline=_bool("RAG_OFFLINE", False),
    )
