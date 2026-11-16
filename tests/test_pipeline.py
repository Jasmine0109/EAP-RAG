"""End-to-end tests: temporary index + hashing embedder + offline generation. No network, no data/."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rag.config import Config
from rag.embed import HashingEmbedder
from rag.pipeline import Rag
from rag.store import DimMismatch


def make_config(root: Path, *, dim: int = 64, top_k: int = 2) -> Config:
    return Config(
        data_dir=root,
        index_path=root / "index" / "index.sqlite3",
        chunk_size=200,
        chunk_overlap=20,
        top_k=top_k,
        embed_dim=dim,
    )


class RagPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.raw = self.root / "raw"
        self.raw.mkdir()
        (self.raw / "cats.md").write_text(
            "# Cats\n\nCats love sunbathing and sleep sixteen hours a day.\n", encoding="utf-8"
        )
        (self.raw / "dogs.md").write_text(
            "# Dogs\n\nDogs need two walks a day and love chasing balls.\n", encoding="utf-8"
        )
        self.rag = Rag(config=make_config(self.root), embedder=HashingEmbedder(64))

    def tearDown(self) -> None:
        self.rag.close()
        self._tmp.cleanup()

    def test_ingest_and_retrieve_ranks_relevant_doc(self) -> None:
        stats = self.rag.ingest([self.raw])
        self.assertEqual(stats.documents, 2)
        self.assertGreater(stats.chunks, 0)

        hits = self.rag.retrieve("What do cats like?", k=1)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].chunk.source, "cats.md")

    def test_ask_offline_returns_context(self) -> None:
        self.rag.ingest([self.raw])
        answer = self.rag.ask("How many walks do dogs need?", offline=True)
        self.assertEqual(answer.mode, "offline")
        self.assertTrue(answer.hits)
        self.assertIn("dogs.md", answer.text)

    def test_reingest_is_idempotent(self) -> None:
        self.rag.ingest([self.raw])
        first = self.rag.store.count()
        self.rag.ingest([self.raw])
        self.assertEqual(self.rag.store.count(), first)

    def test_empty_index_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            self.rag.retrieve("any question")

    def test_dim_mismatch_is_reported(self) -> None:
        self.rag.ingest([self.raw])
        other = Rag(config=make_config(self.root, dim=32), embedder=HashingEmbedder(32))
        try:
            with self.assertRaises(DimMismatch):
                other.ingest([self.raw])
        finally:
            other.close()

    def test_missing_path_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self.rag.ingest([self.root / "nope"])


if __name__ == "__main__":
    unittest.main()
