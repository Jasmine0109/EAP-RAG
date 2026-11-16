# Golden Dataset

> A golden dataset is a fixed set of **inputs + expectations + judging rules**. It is the only asset a model cannot replace.

## Why

Without it, changing embeddings, prompts, or chunking is judged by vibes. With it, you can say "score went from X to Y".

## Anatomy of a case (6 blocks)

| Block | Fields | Purpose |
| --- | --- | --- |
| identity | `id` `theme` `tags` `severity` | identify, filter, prioritize |
| input | `input` (+ `context`, `profile`) | the user's words |
| expected behavior | `behavior` (answer/clarify/refuse/escalate) + `clarify_target` | answer, ask, refuse, or escalate |
| evidence | `sources` | which documents should be cited |
| hard constraints | `must_include` / `must_not_include` | required/forbidden phrases |
| scoring + metadata | `rubric` `smoke` `owner` `notes` `created` | quality scores, CI flag, provenance |

## Why field names are English

Field names are identifiers (keys), conventionally `snake_case` English so code and tools can read them. The **content** is English too for this product.

## Rubric: 5 dimensions

| Field | Meaning | Why it matters |
| --- | --- | --- |
| `empathy` | acknowledge feelings, no judgment | advice lands only after feeling heard |
| `appropriateness` | match the situation and severity | mismatched tone feels dismissive or alarming |
| `actionability` | one concrete next step | the difference from a generic chatbot |
| `boundary` | no diagnosis, no medication, no overreach | safety floor |
| `citation` | key claims traceable to sources | trust |

Not a universal list; add `safety`, `clarity`, `conciseness` as needed.

## smoke

`smoke: true` → included in the fast CI gate (10–15 cases, must stay green, especially crisis/refusal).

## Directory

```
evals/
├── README.md
├── cases/
│   ├── core-en.yaml                # current baseline v1.0 (English corpus)
│   └── archive/
│       └── core-zh-v0.2.yaml       # old baseline (Chinese corpus), history only
└── reports/                        # eval artifacts (gitignored)
```

## Versions and archiving

| Version | File | Corpus | Status |
| --- | --- | --- | --- |
| v0.2 | `cases/archive/core-zh-v0.2.yaml` | Chinese | archived, not in CI |
| v1.0 | `cases/core-en.yaml` | English | **current baseline** |

Why archive instead of delete: it preserves how we labeled at the time. But it cannot serve as a comparison baseline after the corpus changed. **One comparison, one dataset version.**

## Two-tier strategy

- **Regression set** (`core-en.yaml`, frozen): "did we get worse?"
- **Expansion set** (`expansion.yaml`, rolling — not created yet): "are we covering new cases?"

## Schema validation

Cases are validated by Pydantic models in `evals/validate.py`: missing fields, wrong enums, rubric out of 1–5, duplicate ids → error.

```bash
make eval-check      # or python evals/validate.py
```

> There is no universal golden-dataset format (OpenAI Evals / promptfoo / RAGAS / LangSmith differ).
> What matters: define the schema once → validate by machine → version it.

## Building one (8 steps)

1. Define the unit of evaluation (one turn? one task?).
2. Define the taxonomy (behavior, severity, failure mode).
3. Write the annotation guide (with positive/negative examples).
4. Sample from real logs + stratify + adversarial cases.
5. Pilot with 10–20 cases and two annotators.
6. Calibrate until κ ≥ 0.6; revise the guide.
7. Scale with human + LLM-synthesized variants (human-filtered).
8. Freeze and version it.

## Size

| Purpose | Size |
| --- | --- |
| Explore a single issue | ~10 |
| Probe model boundaries | ~10 hard cases |
| CI on larger changes | 100–1000 (needs production distribution) |
| Guardrail penetration | large and growing |

## Runner (not built yet)

```bash
python -m eval run --suite smoke
```

Metrics: behavior accuracy, source recall@5, citation support, must_include coverage, must_not_include violations (must be 0), rubric mean, latency, cost.
