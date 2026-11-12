"""把 corpus/processed/articles.jsonl 写成 markdown 并建索引（切块+真嵌入+SQLite）。

用法：python pipeline/build_index.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag.pipeline import Rag  # noqa: E402


def slugify(s: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "_", s)[:40] or "article"


def main() -> int:
    src = ROOT / "corpus" / "processed" / "articles.jsonl"
    out_dir = ROOT / "data" / "raw" / "corpus"
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in out_dir.rglob("*.md"):
        p.unlink()

    articles = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    for i, a in enumerate(articles):
        d = out_dir / a["source"]
        d.mkdir(parents=True, exist_ok=True)
        fname = f"{i:03d}-{slugify(a['title'])}.md"
        (d / fname).write_text(f"# {a['title']}\n\n{a['text']}", encoding="utf-8")
    print(f"wrote {len(articles)} md files -> data/raw/corpus/")

    rag = Rag()
    try:
        rag.store.reset()
        stats = rag.ingest([out_dir])
    finally:
        rag.close()
    print(f"indexed: {stats.documents} docs, {stats.chunks} chunks, dim={rag.embedder.dim if hasattr(rag.embedder, 'dim') else '?'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
