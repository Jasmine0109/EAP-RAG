PY ?= python3
export PYTHONPATH := src

.DEFAULT_GOAL := help

help: ## 显示所有目标
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## 可编辑安装（可选，开发更顺手）
	$(PY) -m pip install -e .

test: ## 跑全部单元测试
	$(PY) -m unittest discover -s tests -v

ingest: ## 把 data/raw 下的文档建进索引
	$(PY) -m rag ingest data/raw

reingest: ## 清空索引后重建
	$(PY) -m rag ingest data/raw --reset

ask: ## 提问：make ask Q="你的问题"
	$(PY) -m rag ask "$(Q)"

search: ## 只检索不生成：make search Q="关键词"
	$(PY) -m rag search "$(Q)"

stats: ## 看索引里有多少文档和块
	$(PY) -m rag stats

reset: ## 删除索引
	$(PY) -m rag reset --yes

demo: ## 一条命令验证骨架可用（离线、无需模型）
	$(PY) -m rag ingest data/raw --reset
	$(PY) -m rag ask "文档怎么切块？" --offline

clean: ## 清理缓存
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache build dist *.egg-info

.PHONY: help install test ingest reingest ask search stats reset demo clean
