"""领域数据结构。保持极简：只有块、命中、答案三种东西。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Chunk:
    """文档切出来的一块。text 是要进 prompt 的正文。"""

    doc_id: str          # 相对路径，稳定且人类可读
    source: str          # 展示用的来源（原文件名）
    index: int           # 块在文档内的序号，从 0 开始
    heading: str         # 所属小节标题，用于回答时标注出处
    text: str

    @property
    def id(self) -> str:
        return f"{self.doc_id}:{self.index}"


@dataclass(slots=True)
class Hit:
    """一次检索结果：块 + 相似度分数（越大越相关）。"""

    chunk: Chunk
    score: float


@dataclass(slots=True)
class Answer:
    """最终回复。mode 区分走了 LLM 还是只做了检索。"""

    text: str
    hits: list[Hit] = field(default_factory=list)
    mode: str = "llm"  # "llm" | "offline"


@dataclass(slots=True)
class IngestStats:
    """一次入库的统计，CLI 直接打印。"""

    documents: int = 0
    chunks: int = 0
    skipped: int = 0
