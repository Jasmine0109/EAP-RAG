"""Document loading and chunking.

Chunking strategy (deliberately conservative):
- split on blank lines (paragraphs), prefer cutting between paragraphs;
- a chunk never exceeds chunk_size characters (long paragraphs are hard-split at sentence ends);
- keep up to `overlap` characters of the tail when it fits, otherwise skip the overlap —
  never produce an oversized chunk.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from .types import Chunk

TEXT_SUFFIXES = {".md", ".markdown", ".txt"}
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
_PARAGRAPH_RE = re.compile(r"\n\s*\n")
_SENTENCE_END = "。！？!?；;."


def iter_files(root: Path) -> Iterator[Path]:
    """Yield ingestable files; skip hidden directories (.git, .venv, ...)."""
    if root.is_file():
        if root.suffix.lower() in TEXT_SUFFIXES:
            yield root
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        yield path


def doc_id_for(path: Path, base: Path) -> str:
    """Use the relative path as doc_id: readable and stable."""
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.name


def _heading_of(paragraph: str) -> str | None:
    first = paragraph.splitlines()[0].strip()
    match = _HEADING_RE.match(first)
    return match.group(1).strip() if match else None


def _split_long(paragraph: str, size: int) -> list[str]:
    """Split an oversized paragraph into pieces of at most `size` chars."""
    if len(paragraph) <= size:
        return [paragraph]
    pieces: list[str] = []
    rest = paragraph
    while len(rest) > size:
        window = rest[:size]
        cut = max((window.rfind(ch) for ch in _SENTENCE_END), default=-1)
        cut = cut + 1 if cut >= size // 2 else size
        piece = rest[:cut].strip()
        if piece:
            pieces.append(piece)
        rest = rest[cut:].lstrip()
    if rest:
        pieces.append(rest)
    return pieces


def _join(paragraphs: list[str]) -> str:
    return "\n\n".join(paragraphs)


def _take_tail(paragraphs: list[str], overlap: int) -> list[str]:
    """Take trailing paragraphs whose total length fits in `overlap`."""
    if overlap <= 0:
        return []
    tail: list[str] = []
    total = 0
    for paragraph in reversed(paragraphs):
        extra = len(paragraph) + (2 if tail else 0)
        if total + extra > overlap:
            break
        tail.insert(0, paragraph)
        total += extra
    return tail


def split_text(text: str, size: int = 800, overlap: int = 120) -> list[Chunk]:
    """Split plain text into chunks; fills index and heading."""
    if size <= 0:
        raise ValueError("size must be > 0")
    if not 0 <= overlap < size:
        raise ValueError("overlap must satisfy 0 <= overlap < size")

    paragraphs = [p.strip() for p in _PARAGRAPH_RE.split(text) if p.strip()]
    chunks: list[Chunk] = []
    buf: list[str] = []
    heading = ""          # currently active heading
    chunk_heading = ""    # heading at the start of the current buffer

    def flush() -> None:
        nonlocal buf, chunk_heading
        if not buf:
            return
        chunks.append(
            Chunk(doc_id="", source="", index=len(chunks), heading=chunk_heading, text=_join(buf))
        )
        buf = []
        chunk_heading = ""

    for paragraph in paragraphs:
        found = _heading_of(paragraph)
        if found:
            heading = found
        for piece in _split_long(paragraph, size):
            if buf and len(_join(buf + [piece])) > size:
                tail = _take_tail(buf, overlap)
                flush()
                # keep the overlap only if it still fits
                if tail and len(_join(tail + [piece])) <= size:
                    buf = tail
                    chunk_heading = chunks[-1].heading
            if not buf:
                chunk_heading = heading
            buf.append(piece)

    flush()
    return chunks


def chunk_document(
    text: str,
    *,
    doc_id: str,
    source: str,
    size: int = 800,
    overlap: int = 120,
) -> list[Chunk]:
    """Chunk a document and fill doc_id/source."""
    chunks = split_text(text, size=size, overlap=overlap)
    for chunk in chunks:
        chunk.doc_id = doc_id
        chunk.source = source
    return chunks
