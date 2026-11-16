"""rag — local RAG knowledge base skeleton.

Pipeline: documents → chunk → embed → store → retrieve → prompt → LLM.
"""

__version__ = "0.1.0"

from .config import Config, load
from .pipeline import Rag
from .types import Answer, Chunk, Hit, IngestStats

__all__ = ["Rag", "Config", "load", "Answer", "Chunk", "Hit", "IngestStats", "__version__"]
