"""Configuration: environment variables override defaults.

All paths are resolved relative to the repo root, so the directory can be moved
without editing config. No config-file format yet — env vars are enough here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# src/rag/config.py -> src/rag -> src -> repo root
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
    """Everything one run needs. Immutable so it can be passed around safely."""

    data_dir: Path
    index_path: Path
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 5
    embed_dim: int = 256
    llm_base_url: str = "http://127.0.0.1:8000/v1"
    llm_model: str = "Qwen3.8-27B-4bit"
    llm_api_key: str = "sk-local"
    llm_timeout: int = 120
    offline: bool = False
    db_url: str = ""

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if not 0 <= self.chunk_overlap < self.chunk_size:
            raise ValueError("chunk_overlap must satisfy 0 <= overlap < chunk_size")
        if self.top_k <= 0:
            raise ValueError("top_k must be > 0")
        if self.embed_dim <= 0:
            raise ValueError("embed_dim must be > 0")


def load() -> Config:
    """Build a config from environment variables."""
    data_dir = Path(_str("RAG_DATA_DIR", str(ROOT / "data"))).expanduser()
    return Config(
        data_dir=data_dir,
        index_path=Path(_str("RAG_INDEX_PATH", str(data_dir / "index" / "index.sqlite3"))).expanduser(),
        chunk_size=_int("RAG_CHUNK_SIZE", 800),
        chunk_overlap=_int("RAG_CHUNK_OVERLAP", 120),
        top_k=_int("RAG_TOP_K", 5),
        embed_dim=_int("RAG_EMBED_DIM", 256),
        llm_base_url=_str("RAG_LLM_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/"),
        llm_model=_str("RAG_LLM_MODEL", "Qwen3.8-27B-4bit"),
        llm_api_key=_str("RAG_LLM_API_KEY", "sk-local"),
        llm_timeout=_int("RAG_LLM_TIMEOUT", 120),
        offline=_bool("RAG_OFFLINE", False),
        db_url=_str("RAG_DB_URL", ""),
    )
