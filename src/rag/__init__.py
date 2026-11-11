"""rag —— 本地 RAG 知识库骨架。

链路：文档 → 切块 → 向量化 → SQLite 存档 → 余弦检索 → 片段 + 问题 → LLM。
"""

__version__ = "0.1.0"

from .config import Config, load
from .pipeline import Rag
from .types import Answer, Chunk, Hit, IngestStats

__all__ = ["Rag", "Config", "load", "Answer", "Chunk", "Hit", "IngestStats", "__version__"]
