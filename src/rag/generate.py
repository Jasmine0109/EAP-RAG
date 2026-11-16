"""Generation: turn retrieved chunks into a prompt, call an OpenAI-compatible LLM,
and fall back to retrieval-only output when the LLM is unavailable.

No vendor lock-in: llama.cpp / MLX / Ollama / vLLM all expose /v1/chat/completions.
Standard library only (urllib).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Sequence

from .types import Hit

SYSTEM_PROMPT = (
    "You are a warm, careful workplace mental-health support assistant. Rules: "
    "1) Empathize before responding. "
    "2) If the user only gives a vague feeling (e.g. 'stressed') without saying what happened, "
    "ask one open question instead of jumping to advice. "
    "3) Only use the provided passages; cite them with [n]. "
    "4) Never diagnose, never discuss medication, never give treatment plans, "
    "never replace professional care. "
    "5) Give one concrete micro-action. "
    "6) If the passages do not answer the question, say so honestly."
)


class LLMError(RuntimeError):
    """LLM call failed (unreachable, timeout, malformed response)."""


def build_messages(question: str, hits: Sequence[Hit]) -> list[dict[str, str]]:
    blocks = []
    for i, hit in enumerate(hits, 1):
        where = f"{hit.chunk.source} § {hit.chunk.heading}" if hit.chunk.heading else hit.chunk.source
        blocks.append(f"[{i}] Source: {where}\n{hit.chunk.text}")
    user = "Passages:\n\n" + "\n\n".join(blocks) + f"\n\nQuestion: {question}\n\nAnswer:"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


class LLMClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000/v1",
        model: str = "Qwen3.8-27B-4bit",
        api_key: str = "sk-local",
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.load(response)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise LLMError(f"cannot reach LLM ({self.base_url}): {exc}") from exc
        except json.JSONDecodeError as exc:
            raise LLMError("LLM returned non-JSON") from exc
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"LLM response is not OpenAI-compatible: {str(data)[:200]}") from exc


def offline_answer(question: str, hits: Sequence[Hit]) -> str:
    """Fallback when no LLM is available: show the most relevant passages."""
    if not hits:
        return "No relevant passages found. Make sure the index is built: rag ingest <path>"
    lines = ["(Offline mode: LLM not called; showing retrieved passages.)"]
    for i, hit in enumerate(hits, 1):
        where = f"{hit.chunk.source} § {hit.chunk.heading}" if hit.chunk.heading else hit.chunk.source
        lines.append(f"[{i}] {where} (score {hit.score:.3f})\n{hit.chunk.text}")
    return "\n\n".join(lines)
