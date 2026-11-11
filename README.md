# rag · 本地 RAG 知识库骨架

把 `data/raw` 里的文档变成可检索的索引：提问时先搜出相关片段，
再把片段和问题一起交给 LLM。默认配置对齐本机环境，**开箱即可跑通**，
三个关键零件（嵌入 / 存储 / 生成）都留了替换接口。

```
文档 ──► 切块 ──► 向量化 ──► SQLite 存档
                                  │
提问 ──► 向量化 ──► 余弦检索 ──► top-k 片段 ──► prompt ──► LLM ──► 带引用的回答
```

## 30 秒验证

```bash
make demo     # 入库示例文档 + 离线提问：不联网、不需要模型
make test     # 14 个单元测试
```

然后换成你自己的资料：

```bash
make ingest                                  # 把 data/raw 全部建进索引
make ask Q="文档怎么切块？"                   # 需要本地 LLM 在 :8000 运行
PYTHONPATH=src python3 -m rag ask "文档怎么切块？" --offline  # 不调 LLM，只看检索片段
```

## 目录结构

```
rag/
├── data/
│   ├── raw/            # 唯一事实来源：放你的 md / txt
│   ├── processed/      # 预留：清洗、转换后的中间产物
│   └── index/          # 索引文件（gitignore，可随时重建）
├── docs/               # 项目文档：模块地图、架构决策
├── src/rag/
│   ├── config.py       # 环境变量 → 不可变 Config
│   ├── types.py        # Chunk / Hit / Answer
│   ├── ingest.py       # 读文件、切块
│   ├── embed.py        # 向量化（默认哈希嵌入）
│   ├── store.py        # SQLite + 暴力余弦检索
│   ├── generate.py     # prompt 拼装、OpenAI 兼容调用、离线兜底
│   ├── pipeline.py     # 编排：ingest / retrieve / ask
│   └── cli.py          # 命令行入口
├── tests/              # unittest，标准库，零依赖
├── Makefile
└── pyproject.toml
```

## 命令

| 命令 | 作用 |
| --- | --- |
| `make demo` | 一条命令验证骨架可用（离线） |
| `make ingest` | 入库 `data/raw`；`make reingest` 先清空再建 |
| `make ask Q="…"` | 检索 + 生成；`--offline` 可跳过 LLM |
| `make search Q="…"` | 只检索，打印命中与分数 |
| `make stats` | 索引里有多少文档 / 块 / 维度 |
| `make reset` | 清空索引（`--yes` 已内置） |
| `make test` | 全部单元测试 |

不用 Make 也行：`PYTHONPATH=src python3 -m rag <命令>`，或 `pip install -e .` 后直接用 `rag`。

## 配置

全部走环境变量（见 `.env.example`），默认值即本机可用配置。最常改的四个：

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `RAG_LLM_BASE_URL` | `http://127.0.0.1:8000/v1` | 任意 OpenAI 兼容服务；**别写 8080**（那是 DSH GUI） |
| `RAG_LLM_MODEL` | `qwen3.8-27b-local` | 服务端实际上报的模型名 |
| `RAG_EMBED_DIM` | `256` | 换嵌入模型时同步改，并重建索引 |
| `RAG_TOP_K` | `5` | 每次喂给 LLM 的片段数 |

## 换零件

**换成真嵌入模型**（第一步升级，收益最大）：

```python
# src/rag/embed.py 的 build_embedder 里换成任意实现，只要满足 dim + embed()
class SentenceTransformerEmbedder:
    def __init__(self, name="BAAI/bge-small-zh-v1.5"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts):
        return self.model.encode(list(texts), normalize_embeddings=True)
```

换完 `rag reset && rag ingest data/raw`，维度不一致时存储层会直接报错提醒。

**换成向量库**：实现 `Store` 的 `replace_doc / search / count / stats / reset`
五个方法即可，`pipeline.py` 不用动。

**换成别的生成服务**：`LLMClient` 只要求 `chat(messages) -> str`，
Anthropic / Ollama 原生协议都可以包一层。

## 设计取舍

- **哈希嵌入是占位，不是方案。** 它靠词面重合，中文单字 + 相邻二元组，能跑通链路，
  但同义改写检索不到。这是有意的：先把管线跑通，再换模型。
- **SQLite + 暴力余弦**：几万块以内毫秒级，零服务、单文件可拷走。
  上到十万级再换 sqlite-vec / FAISS。
- **索引是派生物**：`data/raw` 才是事实来源，索引随时可删可重建。
  `replace_doc` 幂等，同一篇改完重跑 ingest 不会产生重复块。
- **零重依赖**：只依赖 numpy；测试用标准库 unittest；HTTP 用 urllib。
  骨架阶段少装一个包，就少一个坏掉的理由。

## 已知限制

- 只读 `.md / .markdown / .txt`，UTF-8；PDF、docx 需要先在 `ingest.iter_files` 前加转换。
- 切块按字符数 + 空行段落，不认 Markdown 代码块/表格边界。
- 没有增量更新、没有查询改写、没有 rerank —— 都在 `docs/01-架构决策.md` 的"下一步"里。

## 下一步

1. 换真嵌入模型（bge-small-zh / Qwen3-Embedding），重建索引对比召回。
2. 加 rerank（交叉编码器）和查询改写。
3. PDF / docx 转换进 `data/processed/`。
4. 建评测集：固定问题 + 期望片段，量出改动前后的召回率。
