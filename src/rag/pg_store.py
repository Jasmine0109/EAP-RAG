"""Postgres + pgvector 存储。接口与 store.Store 一致，可互换。

用法：RAG_DB_URL=postgresql:///eap python pipeline/build_index.py
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
import psycopg2

from .types import Chunk, Hit

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    id        bigserial PRIMARY KEY,
    chunk_id  text NOT NULL UNIQUE,
    doc_id    text NOT NULL,
    source    text NOT NULL,
    idx       int  NOT NULL,
    heading   text NOT NULL,
    text      text NOT NULL,
    embedding vector(512) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks (doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE TABLE IF NOT EXISTS meta (key text PRIMARY KEY, value text NOT NULL);
"""


def _to_pg(vec: np.ndarray) -> str:
    arr = np.asarray(vec, dtype=np.float32)
    return "[" + ",".join(f"{x:.7f}" for x in arr) + "]"


class PostgresStore:
    def __init__(self, dsn: str) -> None:
        self._conn = psycopg2.connect(dsn)
        with self._conn.cursor() as cur:
            cur.execute(_SCHEMA)
        self._conn.commit()
        self._dim = 512

    # ---- 写入 ---------------------------------------------------------

    def replace_doc(self, doc_id: str, chunks: Sequence[Chunk], vectors: np.ndarray) -> None:
        if len(chunks) != len(vectors):
            raise ValueError(f"chunks({len(chunks)}) 与 vectors({len(vectors)}) 数量不一致")
        if not chunks:
            return
        rows = [
            (c.id, c.doc_id, c.source, c.index, c.heading, c.text, _to_pg(v))
            for c, v in zip(chunks, vectors)
        ]
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM chunks WHERE doc_id = %s", (doc_id,))
            cur.executemany(
                "INSERT INTO chunks(chunk_id, doc_id, source, idx, heading, text, embedding) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s::vector)",
                rows,
            )
        self._conn.commit()

    def reset(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute("TRUNCATE chunks RESTART IDENTITY")
            cur.execute("DELETE FROM meta")
        self._conn.commit()

    # ---- 读取 ---------------------------------------------------------

    def count(self) -> int:
        with self._conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM chunks")
            return int(cur.fetchone()[0])

    def stats(self) -> dict[str, int]:
        with self._conn.cursor() as cur:
            cur.execute("SELECT count(*), count(DISTINCT doc_id) FROM chunks")
            chunks, docs = cur.fetchone()
        return {"documents": int(docs), "chunks": int(chunks), "dim": self._dim}

    def search(self, query_vec: np.ndarray, k: int = 5) -> list[Hit]:
        if self.count() == 0:
            return []
        q = _to_pg(query_vec)
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT doc_id, source, idx, heading, text, 1 - (embedding <=> %s::vector) AS score "
                "FROM chunks ORDER BY embedding <=> %s::vector LIMIT %s",
                (q, q, k),
            )
            rows = cur.fetchall()
        return [
            Hit(
                chunk=Chunk(doc_id=r[0], source=r[1], index=r[2], heading=r[3], text=r[4]),
                score=float(r[5]),
            )
            for r in rows
        ]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "PostgresStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
