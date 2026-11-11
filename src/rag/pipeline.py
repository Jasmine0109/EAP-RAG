"""编排：把 ingest / embed / store / generate 串成两个动作 —— 建库、提问。"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .config import Config, load
from .embed import Embedder, build_embedder
from .generate import LLMClient, LLMError, build_messages, offline_answer
from .ingest import chunk_document, doc_id_for, iter_files
from .store import Store
from .types import Answer, Hit, IngestStats


class Rag:
    def __init__(
        self,
        config: Config | None = None,
        *,
        embedder: Embedder | None = None,
        store: Store | None = None,
        llm: LLMClient | None = None,
    ) -> None:
        self.config = config or load()
        self.embedder = embedder or build_embedder(self.config.embed_dim)
        self.store = store or Store(self.config.index_path)
        self._llm = llm

    # ---- 建库 ---------------------------------------------------------

    def ingest(self, paths: Sequence[str | Path], *, reset: bool = False) -> IngestStats:
        if reset:
            self.store.reset()
        stats = IngestStats()
        for raw in paths:
            root = Path(raw).expanduser()
            if not root.exists():
                raise FileNotFoundError(f"路径不存在：{root}")
            base = root if root.is_dir() else root.parent
            for path in iter_files(root):
                try:
                    text = path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    stats.skipped += 1
                    continue
                doc_id = doc_id_for(path, base)
                chunks = chunk_document(
                    text,
                    doc_id=doc_id,
                    source=path.name,
                    size=self.config.chunk_size,
                    overlap=self.config.chunk_overlap,
                )
                if not chunks:
                    stats.skipped += 1
                    continue
                vectors = self.embedder.embed([c.text for c in chunks])
                self.store.replace_doc(doc_id, chunks, vectors)
                stats.documents += 1
                stats.chunks += len(chunks)
        return stats

    # ---- 检索与回答 ---------------------------------------------------

    def retrieve(self, question: str, k: int | None = None) -> list[Hit]:
        if self.store.count() == 0:
            raise RuntimeError("索引是空的。先运行：rag ingest <路径>（或 make ingest）")
        vector = self.embedder.embed([question])
        return self.store.search(vector[0], k=k or self.config.top_k)

    def ask(self, question: str, k: int | None = None, *, offline: bool | None = None) -> Answer:
        hits = self.retrieve(question, k=k)
        use_offline = self.config.offline if offline is None else offline
        if use_offline:
            return Answer(text=offline_answer(question, hits), hits=hits, mode="offline")
        if self._llm is None:
            self._llm = LLMClient(
                base_url=self.config.llm_base_url,
                model=self.config.llm_model,
                api_key=self.config.llm_api_key,
                timeout=self.config.llm_timeout,
            )
        try:
            text = self._llm.chat(build_messages(question, hits))
        except LLMError as exc:
            return Answer(
                text=f"（LLM 调用失败，已退回离线结果：{exc}）\n\n" + offline_answer(question, hits),
                hits=hits,
                mode="offline",
            )
        return Answer(text=text, hits=hits, mode="llm")

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> "Rag":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
