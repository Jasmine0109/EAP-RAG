"""SQLite 向量存储 + 暴力余弦检索。

为什么不是向量数据库：几千到几万块时，一次矩阵乘法（毫秒级）比分页查询还快，
而且零外部服务、单文件可拷走。规模上到十万级再换 sqlite-vec / FAISS / Qdrant，
接口（add / replace_doc / search / reset）保持不动即可。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Sequence

import numpy as np

from .types import Chunk, Hit

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    rowid_  INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id TEXT NOT NULL UNIQUE,
    doc_id   TEXT NOT NULL,
    source   TEXT NOT NULL,
    idx      INTEGER NOT NULL,
    heading  TEXT NOT NULL,
    text     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);

CREATE TABLE IF NOT EXISTS vectors (
    chunk_rowid INTEGER PRIMARY KEY REFERENCES chunks(rowid_) ON DELETE CASCADE,
    vec         BLOB NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class DimMismatch(ValueError):
    """索引维度与当前嵌入维度不一致 —— 只能重建。"""


class Store:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)
        self._dim: int | None = None
        stored = self._meta_get("dim")
        if stored is not None:
            self._dim = int(stored)

    # ---- 元信息 -------------------------------------------------------

    def _meta_get(self, key: str) -> str | None:
        row = self._conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    @property
    def dim(self) -> int | None:
        return self._dim

    def _check_dim(self, dim: int) -> None:
        if self._dim is None:
            self._conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES('dim', ?)", (str(dim),))
            self._dim = dim
        elif self._dim != dim:
            raise DimMismatch(
                f"索引维度是 {self._dim}，当前嵌入维度是 {dim}。"
                f"换嵌入模型后需要重建索引：rag reset && rag ingest <路径>"
            )

    # ---- 写入 ---------------------------------------------------------

    def replace_doc(self, doc_id: str, chunks: Sequence[Chunk], vectors: np.ndarray) -> None:
        """整篇替换：同一 doc_id 重复入库不会产生重复块（幂等）。"""
        if len(chunks) != len(vectors):
            raise ValueError(f"chunks({len(chunks)}) 与 vectors({len(vectors)}) 数量不一致")
        if not chunks:
            return
        vectors = np.asarray(vectors, dtype=np.float32)
        self._check_dim(vectors.shape[1])
        with self._conn:
            self._conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            for chunk, vec in zip(chunks, vectors):
                cur = self._conn.execute(
                    "INSERT INTO chunks(chunk_id, doc_id, source, idx, heading, text) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (chunk.id, chunk.doc_id, chunk.source, chunk.index, chunk.heading, chunk.text),
                )
                self._conn.execute(
                    "INSERT INTO vectors(chunk_rowid, vec) VALUES (?, ?)",
                    (cur.lastrowid, vec.tobytes()),
                )

    def reset(self) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM vectors")
            self._conn.execute("DELETE FROM chunks")
            self._conn.execute("DELETE FROM meta")
        self._dim = None

    # ---- 读取 ---------------------------------------------------------

    def count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])

    def stats(self) -> dict[str, int]:
        docs = int(self._conn.execute("SELECT COUNT(DISTINCT doc_id) FROM chunks").fetchone()[0])
        return {"documents": docs, "chunks": self.count(), "dim": self._dim or 0}

    def search(self, query_vec: np.ndarray, k: int = 5) -> list[Hit]:
        if self.count() == 0:
            return []
        query = np.asarray(query_vec, dtype=np.float32).reshape(-1)
        rows = self._conn.execute(
            "SELECT c.doc_id, c.source, c.idx, c.heading, c.text, v.vec "
            "FROM chunks c JOIN vectors v ON v.chunk_rowid = c.rowid_"
        ).fetchall()
        if not rows:
            return []
        matrix = np.stack([np.frombuffer(row[5], dtype=np.float32) for row in rows])
        scores = matrix @ query
        k = min(k, len(rows))
        top = np.argpartition(-scores, k - 1)[:k]
        top = top[np.argsort(-scores[top])]
        return [
            Hit(
                chunk=Chunk(
                    doc_id=rows[i][0], source=rows[i][1], index=rows[i][2],
                    heading=rows[i][3], text=rows[i][4],
                ),
                score=float(scores[i]),
            )
            for i in top
        ]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
