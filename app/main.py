"""eap-rag 后端：单页 UI + /api/chat（RAG 检索 + 本地 Qwen 生成 + 危机熔断）。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from rag.pipeline import Rag  # noqa: E402

app = FastAPI(title="eap-rag")

_rag: Rag | None = None


def get_rag() -> Rag:
    global _rag
    if _rag is None:
        _rag = Rag()
    return _rag


CRISIS_WORDS = [
    "不想活", "自杀", "自残", "结束生命", "轻生", "活着没意思", "想死",
    "解脱", "伤害自己", "活不下去", "跳楼", "割腕", "想结束",
]

CRISIS_REPLY = (
    "我听到你现在很痛苦，谢谢你愿意把这件事告诉我。你能说出来，这已经很不容易。\n\n"
    "你现在的安全是最重要的，请现在联系（下面是 24 小时有人接听的热线，"
    "电话那头是受过专门训练的人，能更好地帮你）：\n\n"
    "· 全国心理援助热线：12356\n"
    "· 北京心理危机研究与干预中心：010-82951332（24 小时）\n"
    "· 紧急情况请拨 110 / 急救 120\n\n"
    "如果可以，告诉一个你信任的人，别一个人待着。我在这里陪你，但请先打上面的电话。"
)


class ChatIn(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")


@app.post("/api/chat")
def chat(body: ChatIn) -> dict:
    msg = (body.message or "").strip()
    if not msg:
        return {"kind": "error", "answer": "请先说说你的困扰。"}
    if any(w in msg for w in CRISIS_WORDS):
        return {"kind": "crisis", "answer": CRISIS_REPLY, "hits": []}

    rag = get_rag()
    try:
        ans = rag.ask(msg)
    except Exception as exc:  # noqa: BLE001
        return {"kind": "error", "answer": f"出错了：{exc}", "hits": []}

    hits = [
        {
            "source": h.chunk.source,
            "heading": h.chunk.heading,
            "score": round(h.score, 3),
            "text": h.chunk.text[:200],
        }
        for h in ans.hits
    ]
    return {"kind": "answer", "answer": ans.text, "mode": ans.mode, "hits": hits}
