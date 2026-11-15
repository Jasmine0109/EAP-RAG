"""校验 evals/cases/*.yaml：字段类型、枚举、rubric 范围、id 唯一性。

用法：python evals/validate.py（或 make eval-check）
"""
from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases"


class Behavior(str, Enum):
    answer = "answer"
    clarify = "clarify"
    refuse = "refuse"
    escalate = "escalate"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Expected(BaseModel):
    behavior: Behavior
    sources: list[str] = Field(default_factory=list)
    must_include: list[str] = Field(default_factory=list)
    must_not_include: list[str] = Field(default_factory=list)
    clarify_target: str | None = None


class Rubric(BaseModel):
    empathy: int = Field(ge=1, le=5)
    appropriateness: int = Field(ge=1, le=5)
    actionability: int = Field(ge=1, le=5)
    boundary: int = Field(ge=1, le=5)
    citation: int = Field(ge=1, le=5)


class Case(BaseModel):
    id: str
    theme: str
    tags: list[str] = Field(default_factory=list)
    severity: Severity
    input: str
    expected: Expected
    rubric: Rubric
    smoke: bool = False
    owner: str | None = None
    notes: str | None = None


class Dataset(BaseModel):
    version: str
    updated: str
    cases: list[Case]

    @field_validator("version", "updated", mode="before")
    @classmethod
    def _as_text(cls, value: object) -> str:
        # YAML 会把 0.2 解析成 float、2026-11-15 解析成 date，统一转成字符串
        return str(value)


def main() -> int:
    ok = True
    seen: dict[str, str] = {}
    for path in sorted(CASES.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        try:
            ds = Dataset.model_validate(raw)
        except ValidationError as exc:
            ok = False
            print(f"ERROR {path.name}:\n{exc}", file=sys.stderr)
            continue

        for case in ds.cases:
            if case.id in seen:
                ok = False
                print(f"ERROR {path.name}: 重复 id {case.id}（另一处：{seen[case.id]}）", file=sys.stderr)
            seen[case.id] = path.name

        sev = {s.value: sum(1 for c in ds.cases if c.severity == s) for s in Severity}
        print(
            f"{path.name}: {len(ds.cases)} 条 | v{ds.version} | "
            f"smoke {sum(c.smoke for c in ds.cases)} | severity {sev}"
        )

    if ok:
        print("OK：全部用例通过 schema 校验")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
