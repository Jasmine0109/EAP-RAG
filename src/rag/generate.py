"""生成：把检索片段拼成 prompt，交给 OpenAI 兼容接口，失败时退回离线片段。

不绑定任何厂商 —— llama.cpp / MLX / Ollama / vLLM 都暴露 /v1/chat/completions。
只用标准库 urllib，不引入 HTTP 依赖。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Sequence

from .types import Hit

SYSTEM_PROMPT = (
    "你是一个温柔、克制的职场心理支持助手。规则："
    "1) 先共情，再回应；"
    "2) 如果用户只说了笼统的感受（比如「压力大」）但没说具体发生了什么，"
    "先共情并问一个开放问题，不要急着给建议；"
    "3) 只依据用户提供的片段回答，引用出处用 [序号]，序号对应片段编号；"
    "4) 不做任何诊断、不开药、不给治疗建议、不替代心理咨询；"
    "5) 给出一个具体可执行的小建议；"
    "6) 片段不足以回答时诚实说明，不要编造。"
)


class LLMError(RuntimeError):
    """调用 LLM 失败（连不上、超时、返回格式不对）。"""


def build_messages(question: str, hits: Sequence[Hit]) -> list[dict[str, str]]:
    blocks = []
    for i, hit in enumerate(hits, 1):
        where = f"{hit.chunk.source} § {hit.chunk.heading}" if hit.chunk.heading else hit.chunk.source
        blocks.append(f"[{i}] 来源：{where}\n{hit.chunk.text}")
    user = "片段：\n\n" + "\n\n".join(blocks) + f"\n\n问题：{question}\n\n回答："
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


class LLMClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000/v1",
        model: str = "qwen3.8-27b-local",
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
            raise LLMError(f"连不上 LLM（{self.base_url}）：{exc}") from exc
        except json.JSONDecodeError as exc:
            raise LLMError("LLM 返回的不是 JSON") from exc
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"LLM 返回结构不符合 OpenAI 协议：{str(data)[:200]}") from exc


def offline_answer(question: str, hits: Sequence[Hit]) -> str:
    """不调用 LLM 时的兜底：直接把最相关原文摆出来，至少可自查。"""
    if not hits:
        return "没有检索到相关内容。先确认已入库：rag ingest <路径>"
    lines = ["（离线模式：未调用 LLM，以下是检索到的原文片段）"]
    for i, hit in enumerate(hits, 1):
        where = f"{hit.chunk.source} § {hit.chunk.heading}" if hit.chunk.heading else hit.chunk.source
        lines.append(f"[{i}] {where}（相似度 {hit.score:.3f}）\n{hit.chunk.text}")
    return "\n\n".join(lines)
