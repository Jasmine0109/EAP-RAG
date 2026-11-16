# Data Pipeline

> Goal: crawl whitelisted sources → clean → chunk → embed → store (Postgres/pgvector or SQLite) so the assistant can retrieve grounded passages.

## 1. Why develop locally but deliver in the cloud

Local is the **kitchen**, the cloud is the **restaurant**. The code is one recipe.

- Iterating locally is fast, free, and inspectable; cloud runs cost money and hide errors behind deploys.
- Crawling and cleaning are full of edge cases; you will hit them on the first ten pages.
- Once the pipeline is solid, switch the storage URL and run the **same code** in the cloud.

## 2. Why not PySpark

Our corpus is hundreds of MB, not TB. A single machine runs the whole pipeline in seconds to minutes.
Spark is for clusters and TB-scale data; using it here is a train for a suitcase.

| Data size | Tool |
| --- | --- |
| < 10 GB | single-machine Python (**we are here**) |
| 10 GB – 1 TB | Polars / DuckDB / Dask |
| > 1 TB | Spark |

## 3. Four stages

```
① crawl      fetch whitelisted URLs → corpus/raw/ (HTML)
② extract    HTML → text, strip nav/ads → corpus/processed/articles.jsonl
③ chunk      split into blocks with heading/source metadata
④ embed+load bge-small-zh (512-d) → Postgres + pgvector (or SQLite)
```

Each stage is a separate script and can be re-run independently.

## 4. Storage: cold vs hot

| Data | Where | Why |
| --- | --- | --- |
| Raw HTML, cleaned JSONL | `corpus/` (local), object storage later | large, rarely read |
| Chunks + vectors | Postgres + pgvector (or SQLite) | queried at runtime |

## 5. Sources (US)

| Source | Content | License |
| --- | --- | --- |
| NIMH (NIH) | stress, depression, anxiety, trauma | US federal work (public domain) |
| MedlinePlus (NIH) | depression, anxiety, stress, mental health, occupational health | public domain |
| SAMHSA | mental health, national helpline, 988 | public domain |
| OSHA | workplace stress | public domain |
| WHO | mental health at work, depression, anxiety | CC BY-NC-SA |

Blocked from this machine: CDC/NIOSH (403 anti-bot), APA (JS-rendered).

## 6. Local checklist

1. `python3 pipeline/crawl.py` → `corpus/processed/articles.jsonl`
2. Inspect titles and text length.
3. `RAG_DB_URL=postgresql:///eap python3 pipeline/build_index.py`
4. Spot-check retrieval: `Rag().retrieve("...")`
5. Serve the app with the same `RAG_DB_URL`.

## 7. Next

- Chunking experiment: compare chunk sizes (400 / 800 / 1200) on retrieval recall.
- Add more relationship/CBT sources.
- Move raw storage to object storage (R2/S3) when deploying.
