# Docs Index

This directory holds two kinds of documents: **project docs** (how this product is built) and **learning notes** (RAG/Agent concepts).

```
docs/
├── PROJECT.md          ← main: product, architecture, roadmap
├── MVP-DESIGN.md       ← interaction: intake flow, answer card, crisis
├── DATA-PIPELINE.md    ← data: crawl → clean → chunk → embed → store
├── SAFETY-DESIGN.md    ← safety: self-help skills, hard boundaries
├── QA-LOG.md           ← log: questions asked and answers given
└── learning/
    └── RAG-AND-AGENT.md   ← concepts (Chinese, kept as-is)
```

## Find by purpose

| I want to… | Read |
| --- | --- |
| understand what we are building | [PROJECT](PROJECT.md) |
| see the conversation/UI design | [MVP-DESIGN](MVP-DESIGN.md) |
| understand how data is collected | [DATA-PIPELINE](DATA-PIPELINE.md) |
| know the safety boundaries | [SAFETY-DESIGN](SAFETY-DESIGN.md) |
| review the discussion log | [QA-LOG](QA-LOG.md) |
| revise RAG/Agent concepts | [Learning notes (Chinese)](learning/RAG-AND-AGENT.md) |

## Why these files are not merged

They are complementary, not redundant: the project doc covers *what/why*, the MVP design covers *interaction*, the pipeline covers *data*, safety covers *boundaries*, and the learning notes cover *concepts*. Merging them would make the main doc bloated and hard to maintain.
