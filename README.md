# eap-rag · Workplace Mental Health Support Assistant

Anyone can open a web page, describe what's bothering them (work stress, relationships, career plateau, anxiety, low mood, insomnia), and get an answer that is **grounded, bounded, and actionable** — retrieved from authoritative sources, with citations. Crisis signals trigger an immediate escalation.

> Input: "I've been really stressed at work and can't sleep."
> → Empathize, then run a short **intake** (what happened, what hurts most, feelings) before giving advice.
>
> Input: "I don't want to be alive anymore." → **Escalate**: 988 / 911, no advice, no questions.

## Status

MVP runs locally end-to-end: crawler → `bge-small-zh-v1.5` embeddings → Postgres/pgvector (or SQLite) → FastAPI chat UI → local Qwen with citations + crisis escalation.

## Run locally

```bash
python3 -m pip install fastapi uvicorn trafilatura lxml_html_clean \
  "sentence-transformers>=3.0" "transformers>=4.40" certifi psycopg2-binary pypdf

python3 pipeline/crawl.py            # crawl whitelisted sources → corpus/processed/articles.jsonl
python3 pipeline/build_index.py      # chunk + embed → SQLite (data/index/index.sqlite3)

PYTHONPATH=src python3 -m uvicorn app.main:app --port 8081
# open http://127.0.0.1:8081
```

Using Postgres + pgvector instead of SQLite:

```bash
createdb eap
psql -d eap -c "create extension vector"
RAG_DB_URL=postgresql:///eap python3 pipeline/build_index.py
RAG_DB_URL=postgresql:///eap PYTHONPATH=src python3 -m uvicorn app.main:app --port 8081
```

## Docs

| Doc | Content |
| --- | --- |
| [Docs index](docs/README.md) | what each doc is, where to start |
| [PROJECT](docs/PROJECT.md) | product, architecture, roadmap |
| [MVP-DESIGN](docs/MVP-DESIGN.md) | intake flow, answer card, crisis design |
| [DATA-PIPELINE](docs/DATA-PIPELINE.md) | crawl → clean → chunk → embed |
| [SAFETY-DESIGN](docs/SAFETY-DESIGN.md) | self-help skills, hard boundaries |
| [QA-LOG](docs/QA-LOG.md) | questions and answers |
| [Learning notes (Chinese)](docs/learning/RAG-AND-AGENT.md) | RAG/Agent concepts |

## Repository layout

```
eap-rag/
├── app/            # FastAPI + single-page chat UI
├── pipeline/       # crawl.py, build_index.py
├── src/rag/        # core: config/types/ingest/embed/store/pg_store/generate/pipeline
├── corpus/         # seeds.json (whitelist), raw/, processed/
├── data/           # index (SQLite, gitignored)
├── evals/          # golden set (core-en.yaml) + validator
└── docs/           # project docs + learning/
```

## Golden set

`evals/cases/core-en.yaml` (v1.0) is the current baseline, written against the English corpus.
The old Chinese baseline is archived at `evals/cases/archive/core-zh-v0.2.yaml` for history only.

```bash
make eval-check     # validate the golden set against the Pydantic schema
```

## Next

1. Build the eval runner (run v1.0 → behavior accuracy, source recall, rubric scores).
2. Implement the intake state machine (sessions, stages, safety gate).
3. Chunking experiment: compare chunk sizes on retrieval recall.

## Boundaries

This is a **reference implementation / portfolio project**, not a production EAP service.
It does not diagnose, treat, or replace professional care; crisis responses only escalate.
Source licensing (WHO CC BY-NC-SA, etc.) must be re-checked before any commercial use.
