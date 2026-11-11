"""切块逻辑的单元测试：边界比功能更值得测。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rag.ingest import chunk_document, iter_files, split_text


class SplitTextTest(unittest.TestCase):
    def test_single_short_text_is_one_chunk(self) -> None:
        chunks = split_text("短文本", size=100, overlap=10)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].text, "短文本")
        self.assertEqual(chunks[0].index, 0)

    def test_chunks_never_exceed_size(self) -> None:
        text = "\n\n".join("段落" * 20 for _ in range(20))  # 每段 40 字
        chunks = split_text(text, size=100, overlap=30)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.text), 100, chunk.text)

    def test_overlap_carries_tail_when_it_fits(self) -> None:
        paragraphs = [chr(ord("A") + i) * 20 for i in range(6)]
        chunks = split_text("\n\n".join(paragraphs), size=100, overlap=30)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(chunks[1].text.startswith("D" * 20), chunks[1].text[:40])

    def test_long_paragraph_is_hard_split(self) -> None:
        chunks = split_text("字" * 250, size=100, overlap=0)
        self.assertEqual(len(chunks), 3)
        self.assertTrue(all(len(c.text) <= 100 for c in chunks))

    def test_heading_is_tracked(self) -> None:
        text = "# 标题一\n\n" + "x" * 60 + "\n\n## 标题二\n\nyyy"
        chunks = split_text(text, size=70, overlap=0)
        self.assertEqual(chunks[0].heading, "标题一")
        self.assertEqual(chunks[-1].heading, "标题二")

    def test_invalid_params_rejected(self) -> None:
        with self.assertRaises(ValueError):
            split_text("x", size=0)
        with self.assertRaises(ValueError):
            split_text("x", size=10, overlap=10)


class ChunkDocumentTest(unittest.TestCase):
    def test_ids_and_source_are_filled(self) -> None:
        chunks = chunk_document("正文", doc_id="notes/a.md", source="a.md", size=100, overlap=0)
        self.assertEqual(chunks[0].doc_id, "notes/a.md")
        self.assertEqual(chunks[0].source, "a.md")
        self.assertEqual(chunks[0].id, "notes/a.md:0")


class IterFilesTest(unittest.TestCase):
    def test_skips_hidden_and_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.md").write_text("a", encoding="utf-8")
            (root / "b.txt").write_text("b", encoding="utf-8")
            (root / "c.pdf").write_bytes(b"%PDF")
            (root / ".git").mkdir()
            (root / ".git" / "d.md").write_text("d", encoding="utf-8")
            (root / "sub").mkdir()
            (root / "sub" / "e.md").write_text("e", encoding="utf-8")

            names = {p.name for p in iter_files(root)}
            self.assertEqual(names, {"a.md", "b.txt", "e.md"})


if __name__ == "__main__":
    unittest.main()
