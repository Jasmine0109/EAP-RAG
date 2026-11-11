"""文档加载与切块。

切块策略（有意保守，方便先跑通）：
- 以空行为段落边界，优先在段落之间切；
- 单块不超过 chunk_size 字符（超长段落按句末硬切）；
- 块间尽量保留 overlap 字符的尾部内容，但**放不下就放弃重叠**，
  保证任何块都不会超过 chunk_size —— 宁可少重叠，不要超长块。
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from .types import Chunk

TEXT_SUFFIXES = {".md", ".markdown", ".txt"}
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
_PARAGRAPH_RE = re.compile(r"\n\s*\n")
_SENTENCE_END = "。！？!?；;"


def iter_files(root: Path) -> Iterator[Path]:
    """列出 root 下所有可入库文件；隐藏目录（.git、.venv 等）直接跳过。"""
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
    """doc_id 用相对路径，既可读又稳定。"""
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.name


def _heading_of(paragraph: str) -> str | None:
    first = paragraph.splitlines()[0].strip()
    match = _HEADING_RE.match(first)
    return match.group(1).strip() if match else None


def _split_long(paragraph: str, size: int) -> list[str]:
    """把超长段落切成每段不超过 size 字符，尽量在句末断开。"""
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
    """从段落尾部取几段，总长不超过 overlap。"""
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
    """把纯文本切成 Chunk 列表，index 和 heading 由本函数填好。"""
    if size <= 0:
        raise ValueError("size 必须大于 0")
    if not 0 <= overlap < size:
        raise ValueError("overlap 必须满足 0 <= overlap < size")

    paragraphs = [p.strip() for p in _PARAGRAPH_RE.split(text) if p.strip()]
    chunks: list[Chunk] = []
    buf: list[str] = []
    heading = ""          # 当前生效的小节标题
    chunk_heading = ""    # 当前缓冲块开头时的标题

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
                # 重叠部分放得下才带上，否则放弃（保证块不超长）
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
    """切块并补齐 doc_id / source。"""
    chunks = split_text(text, size=size, overlap=overlap)
    for chunk in chunks:
        chunk.doc_id = doc_id
        chunk.source = source
    return chunks
