# eap-rag · 职场心理与生活支持助手

任何人打开一个网页，把困扰说出来（工作压力、人际关系、晋升瓶颈、焦虑、抑郁情绪、失眠……），
系统从知识库里检索权威科普与自助方法，给出**有出处、有边界、可执行**的回答；出现危机信号直接转介。

> 输入：「最近工作压力很大，晚上睡不着，白天没精神」
> → 先共情 + 追问具体情境（没搞懂原因不给建议）
> → 再给回答卡：共情 + 建议 + 一个可执行动作 + 何时求助 + 来源引用
>
> 输入：「活着没意思」→ **熔断**，只给热线和求助路径，不生成任何建议。

## 当前状态

**MVP 已本地跑通**：爬虫 → bge-small-zh 嵌入建库 → FastAPI 聊天 UI → 本地 Qwen 带引用回答 + 危机熔断。

## 本地运行

```bash
python3 -m pip install fastapi uvicorn trafilatura lxml_html_clean "sentence-transformers>=3.0" "transformers>=4.40" certifi
python3 pipeline/crawl.py            # 抓语料 → corpus/processed/articles.jsonl
python3 pipeline/build_index.py      # 切块+嵌入 → data/index/index.sqlite3
PYTHONPATH=src python3 -m uvicorn app.main:app --port 8081
# 浏览器打开 http://127.0.0.1:8081
```

## 文档

| 文档 | 内容 |
| --- | --- |
| [项目文档](docs/项目文档.md) | 问题、产品、架构、详细设计、edge cases、部署、路线 |
| [MVP 设计](docs/MVP-设计.md) | 回答卡交互、先问清楚再回答、危机转介 |
| [数据 pipeline](docs/数据pipeline.md) | 抓取→清洗→切块→入库；本地开发、云端交付 |
| **[学习笔记](docs/learning/README.md)** | RAG 从 0 到 1、Agent 多轮架构、观测层、质量 rubric、金标、记忆 |
| [问答与不懂清单](docs/问答与不懂清单.md) | 逐条问题与答案，持续更新 |

## 仓库结构

```
eap-rag/
├── app/            # FastAPI + 单页聊天 UI（app/main.py, app/static/index.html）
├── pipeline/       # crawl.py（抓取）、build_index.py（切块+嵌入+入库）
├── src/rag/        # 核心：config / types / ingest / embed / store / generate / pipeline
├── corpus/         # seeds.json（白名单）、raw/（HTML）、processed/（jsonl）
├── data/           # index（SQLite，gitignore）
├── evals/          # 金标种子用例
└── docs/           # 项目文档 + learning/ 学习笔记
```

## 下一步

1. **金标扩到 30 条**，跑出基线指标（Recall@5、引用支撑率、转介召回）——先有尺子。
2. 给 `/api/chat` 加**最小会话状态**（最近几轮 + 当前 goal）。
3. 语料升级为权威源（临床指南 / 官方科普 / 法规），每条带证据等级。
4. 云端部署（R2 + Supabase + Fly），公开可访问。

## 边界

这是**参考实现与作品集项目**，不是可上线的 EAP 服务：
不做诊断、不做治疗、不做危机干预本身；公开演示必须保留免责声明与危机资源；
语料许可（WHO 非商业条款）在商业化前需重新评估。
