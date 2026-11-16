"""Domain types. Keep it minimal: chunk, hit, answer, ingest stats."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Chunk:
    """A piece of a document. `text` is what goes into the prompt."""

    doc_id: str          # relative path, stable and human-readable
    source: str          # display name (original file name)
    index: int           # position inside the document, starting at 0
    heading: str         # section heading, used for citations
    text: str

    @property
    def id(self) -> str:
        return f"{self.doc_id}:{self.index}"


@dataclass(slots=True)
class Hit:
    """One retrieval result: a chunk plus a similarity score (higher is better)."""

    chunk: Chunk
    score: float


@dataclass(slots=True)
class Answer:
    """Final reply. `mode` tells whether an LLM was used."""

    text: str
    hits: list[Hit] = field(default_factory=list)
    mode: str = "llm"  # "llm" | "offline"


@dataclass(slots=True)
class IngestStats:
    """Counters for one ingest run, printed by the CLI."""

    documents: int = 0
    chunks: int = 0
    skipped: int = 0
