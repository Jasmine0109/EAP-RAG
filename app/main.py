"""eap-rag backend: single-page UI + /api/chat (RAG retrieval + local Qwen + crisis gate)."""
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
    "kill myself", "suicide", "suicidal", "end my life", "don't want to live",
    "don't want to be alive", "want to die", "self-harm", "self harm", "hurt myself",
    "no reason to live", "better off dead", "end it all", "can't go on", "just disappear",
]

CRISIS_REPLY = (
    "I can hear how much pain you're in, and I'm glad you told me. That took courage.\n\n"
    "Your safety matters most right now. I can't replace professional crisis support, "
    "but these lines are staffed 24/7 by trained people:\n\n"
    "· 988 Suicide & Crisis Lifeline — call or text 988\n"
    "· SAMHSA National Helpline — 1-800-662-4357\n"
    "· Emergency — call 911\n\n"
    "If you are in immediate danger, call 911 and try to stay with someone you trust. "
    "Would you be willing to call one of these numbers now?"
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
        return {"kind": "error", "answer": "Please tell me what's going on."}
    if any(w in msg.lower() for w in CRISIS_WORDS):
        return {"kind": "crisis", "answer": CRISIS_REPLY, "hits": []}

    rag = get_rag()
    try:
        ans = rag.ask(msg)
    except Exception as exc:  # noqa: BLE001
        return {"kind": "error", "answer": f"Something went wrong: {exc}", "hits": []}

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
