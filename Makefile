PY ?= python3
DB_URL ?= postgresql:///eap
export PYTHONPATH := src

.DEFAULT_GOAL := help

help: ## show targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## install dependencies
	$(PY) -m pip install fastapi uvicorn trafilatura lxml_html_clean "sentence-transformers>=3.0" "transformers>=4.40" certifi psycopg2-binary pypdf

crawl: ## crawl whitelisted sources -> corpus/processed/articles.jsonl
	$(PY) pipeline/crawl.py

index: ## chunk + embed -> Postgres/pgvector (RAG_DB_URL)
	RAG_DB_URL=$(DB_URL) $(PY) pipeline/build_index.py

serve: ## start the chat UI (http://127.0.0.1:8081)
	RAG_DB_URL=$(DB_URL) $(PY) -m uvicorn app.main:app --port 8081

test: ## run unit tests
	$(PY) -m unittest discover -s tests -v

eval-check: ## validate the golden set against the schema
	$(PY) evals/validate.py

clean: ## remove caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache build dist *.egg-info

.PHONY: help install crawl index serve test eval-check clean
