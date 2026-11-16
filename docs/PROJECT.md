# Project: eap-rag

> A workplace mental-health support assistant. Users describe what's bothering them and get a grounded, bounded, actionable answer with citations; crisis signals escalate immediately.

Status: MVP running locally. English corpus (NIMH / MedlinePlus / SAMHSA / OSHA / WHO), Postgres + pgvector, intake flow designed.

## 1. What it is

| Dimension | Content |
| --- | --- |
| For whom | Everyone: employees, managers, anyone with a work/life concern |
| Problems | Work stress, coworker/manager conflict, career plateau, anxiety, low mood, insomnia |
| How it works | Open the web page → chat → grounded answer with sources |
| Differentiator | Intake before advice; one micro-action per answer; escalate on crisis |

## 2. What it is not (red lines)

- No diagnosis, no medication advice, no treatment plans.
- No pretending to be therapy or a crisis service.
- Crisis (self-harm / suicide) → escalate only, nothing else.

## 3. Minimum MVP

1. **Chat UI** — single page; citations expandable.
2. **Knowledge base** — authoritative sources, chunked and embedded.
3. **Retrieval** — query → embed → pgvector top-k.
4. **Generation** — retrieved chunks + question → LLM → cited answer.
5. **Intake flow** — clarify (situation, trigger, feelings) before advice.
6. **Safety** — keyword + intent check → crisis card; never diagnose.

Out of scope for MVP: login, roles, admin dashboard, multi-tenant, cloud deployment, multilingual UI (English only for now).

## 4. Roadmap

| Phase | What | Done when |
| --- | --- | --- |
| MVP | Chat + retrieval + intake + safety | A user can get a cited answer, and a crisis message escalates |
| V1 | Golden set 30–40 cases + runner + metrics | We can say "score went from X to Y" |
| V2 | Admin dashboard + eval comparisons + cloud deploy | Public URL with traces and cost |
| V3 | Better crisis detection, multi-turn memory, more corpus | — |

## 5. Data pipeline

```
whitelist (corpus/seeds.json)
  → crawl (pipeline/crawl.py)        → corpus/raw/ (HTML)
  → extract + clean                  → corpus/processed/articles.jsonl
  → chunk + embed (build_index.py)    → Postgres + pgvector (or SQLite)
```

Sources: NIMH, MedlinePlus, SAMHSA, OSHA, WHO (public-domain or CC BY-NC-SA). CDC/NIOSH and APA are currently blocked by anti-bot or JS rendering.

## 6. Stack

| Layer | Choice | Why |
| --- | --- | --- |
| UI | FastAPI + single-page HTML | fastest path to a working chat |
| Backend | FastAPI (Python) | same language as eval/embeddings |
| Store | Postgres + pgvector (SQLite fallback) | vectors + metadata in one place |
| Embeddings | `bge-small-zh-v1.5` (512-d) | good multilingual retrieval, CPU-friendly |
| LLM | local Qwen (`:8000`, OpenAI-compatible) | free during development; DeepSeek in production |
| Eval | YAML golden set + Pydantic validator | reviewable, diffable, versioned |

## 7. Safety

- Crisis words/intent → **988** (Suicide & Crisis Lifeline) / **911**; no advice, no questions.
- No diagnosis; no medication; no dismissal/retaliation advice.
- Safety rules are code branches, not just prompts.
- See [SAFETY-DESIGN](SAFETY-DESIGN.md).

## 8. Milestones

1. Corpus pipeline (US sources) — done.
2. Postgres + pgvector migration — done.
3. Golden set v1.0 (English) — done.
4. Eval runner — next.
5. Intake state machine — next.
6. Chunking strategy comparison — next.

## 9. Open questions

- English only, or bilingual (English + Chinese)?
- Which crisis numbers to show by default (988 + 911 vs. state-specific)?
- Do we keep conversation history server-side, or keep sessions ephemeral?

## Changelog

- v0.2 — slimmed to framework + MVP; roles removed; golden set workflow added.
- v0.3 — US corpus, Postgres/pgvector, intake flow, golden set v1.0.
