# 金标数据集（Golden Dataset）

## 为什么需要

没有金标，你换嵌入、改 prompt、调切块、换模型，**全都只能说"感觉变好了"**。
金标的作用只有一个：让"改之前 vs 改之后"可比。

它也是项目里**唯一不能被模型替代的资产**——模型可以换，你的专业判断和这批用例换不掉。

## 目录

```
evals/
├── README.md          # 本文件
├── cases/
│   └── core.yaml      # 金标用例（含 smoke 标记）
└── reports/           # 评测产物（gitignore，可重建）
```

## 一条用例长什么样

| 字段 | 含义 |
| --- | --- |
| `id` | 唯一 id |
| `theme` | 主题（工作压力 / 人际 / 晋升 / 焦虑 / 抑郁情绪 / 失眠 / 危机 / 越权 / 政策） |
| `input` | 用户原话（越口语越好） |
| `expected.behavior` | `answer` / `clarify` / `refuse` / `escalate` |
| `expected.sources` | 期望命中的来源（文章标题或 key），可空 |
| `expected.must_include` | 回答里**必须**出现的要点 |
| `expected.must_not_include` | 回答里**禁止**出现的表述 |
| `rubric` | 质量分 1–5：共情 / 恰当 / 可执行 / 边界 / 引用 |
| `smoke` | `true` 进 CI 冒烟集（含危机/拒答门禁） |

## 怎么建（五步）

1. **定范围**：8 个主题 × 4 种行为，避免只测"会答的题"。
2. **写种子**：10–15 条，专家写，覆盖正常 + 边缘 + 危机。
3. **扩量**：LLM 造变体 → 人工筛（去重、去偏、去"自己会写"的题）。
4. **盲评校准**：1–2 位同行盲评，避免作者偏差。
5. **失败回流**：每次评测/线上翻车，就补一条。

## 写在哪、存在哪

- **源文件在 git**：`evals/cases/*.yaml`。YAML 可读、可 diff、可 review——这是唯一权威。
- **评测结果**是派生物：`evals/reports/*.md` 或数据库，不入库（或单独归档）。
- 数据集带 `version` / `updated`，两次对比必须用同一版。

## 怎么跑（runner 待实现）

```bash
python -m eval run --suite smoke   # 10 条以内，CI 用
python -m eval run --suite full    # 全量
```

评测要算的指标：行为正确率（answer/clarify/refuse/escalate）、来源命中率、引用支撑率、
`must_include` 覆盖率、`must_not_include` 违规率（必须 0）、rubric 均分。

## 当前进度

- v0.1：13 条（含 6 条 smoke 门禁），覆盖 8 个主题。
- 目标：扩到 30–40 条，然后接 runner + LLM 判官。
