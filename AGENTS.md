# 工作区约定（给在此仓库工作的 AI agent）

## 目标

保持这个骨架**可运行、可替换、可解释**。它不是最终产品，是一副骨架：
读代码的人应该在十分钟内看懂数据从哪来到哪去。

## 命令

```bash
make test        # 提交前必跑，14 个测试必须全绿
make demo        # 端到端冒烟：入库 + 离线提问
make ingest      # 重建索引（data/raw → data/index）
```

## 结构不变量

- `src/rag/pipeline.py` 是唯一编排层；模块之间不互相 import 业务逻辑。
- 新能力优先加在对应模块内（读文件 → ingest，算分 → store，prompt → generate）。
- `Store` 与 `Embedder` 的接口是契约：换实现不改调用方。
- 测试不联网、不读 `data/raw`、不写真实索引 —— 一律用 `tempfile` 和临时 Config。

## 编码约定

- Python 3.11+，全量类型注解，`from __future__ import annotations`。
- 注释、文档字符串、CLI 输出用中文；标识符用英文。
- 运行时依赖只有 numpy。**新增依赖前先问用户**，并说明为什么标准库不够。
- 配置只走环境变量 + `config.load()`，不要引入配置文件格式。

## 数据与安全

- `data/raw` 是事实来源；索引是派生物，可随时 `make reset` 重建。
- 不要把真实文档、索引、`.env` 提交进 git（`.gitignore` 已覆盖）。
- 改嵌入维度必须重建索引，`DimMismatch` 会拦下来，不要绕过它。

## 改动后自检

1. `make test`
2. `make demo`（应输出一条带来源的离线回答）
3. 涉及 ingest/store 的改动，额外验证「同一目录 ingest 两次，块数不变」
