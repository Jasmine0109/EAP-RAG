PY ?= python3
export PYTHONPATH := src

.DEFAULT_GOAL := help

help: ## 显示所有目标
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	$(PY) -m pip install fastapi uvicorn trafilatura lxml_html_clean "sentence-transformers>=3.0" "transformers>=4.40" certifi

crawl: ## 抓语料 → corpus/processed/articles.jsonl
	$(PY) pipeline/crawl.py

index: ## 切块+嵌入 → data/index/index.sqlite3
	$(PY) pipeline/build_index.py

serve: ## 启动聊天界面（http://127.0.0.1:8081）
	$(PY) -m uvicorn app.main:app --port 8081

test: ## 单元测试
	$(PY) -m unittest discover -s tests -v

clean: ## 清理缓存
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache build dist *.egg-info

.PHONY: help install crawl index serve test clean
