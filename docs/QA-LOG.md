# QA Log

> Questions asked during the project, with short answers and pointers.

| # | Question | Answer |
| --- | --- | --- |
| 1 | Should we build our own golden dataset? | Yes — without it you cannot tell whether a change made things better |
| 2 | How do we build one? | Define scope → annotation guide → pilot → calibrate (κ ≥ 0.6) → scale → freeze |
| 3 | Where does it live? | `evals/cases/*.yaml`, in git; results are derived artifacts in `evals/reports/` |
| 4 | Do we need multiple datasets? | Split by what you measure: end-to-end, retrieval, safety, multi-turn |
| 5 | What is a regression set vs. expansion set? | Frozen set for "did we get worse"; rolling set for "are we covering new cases" |
| 6 | Why Pydantic validation? | Fields defined ≠ fields correct; it catches enum/range/missing/duplicate errors at load time |
| 7 | What does `smoke: true` mean? | Runs in the fast CI gate on every push; must stay green |
| 8 | Why can't advice be scored right/wrong? | No single correct answer; use a rubric (empathy / appropriateness / actionability / boundary / citation) |
| 9 | What does the runner score? | Its own generation: behavior, source recall, must-include coverage, forbidden words, rubric |
| 10 | Where is the data stored? | Chunks + vectors in Postgres/pgvector (or SQLite); golden set in YAML in git |
| 11 | Why SQLite originally? | Zero install, one file, enough for thousands of chunks |
| 12 | Why move to Postgres + pgvector? | Scale, concurrency, and cloud deployment; same interface |
| 13 | Is RAG part of the agent loop? | Yes — retrieval is a node; index building is outside the loop |
| 14 | Why does the agent need memory/goal state? | LLMs are stateless; state must be re-injected each turn |
| 15 | What did DeepSeek publish? | Model architecture (V3/R1 papers); not the product/agent architecture |
| 16 | How should we evaluate architectures? | Data flow, state, failure modes, eval, cost — not framework names |
| 17 | Why did the corpus change? | Old psychology-popularization pages were irrelevant; we switched to US authoritative sources |
| 18 | Why keep the old golden set? | History — but it cannot serve as a comparison baseline after the corpus change |
| 19 | Why English now? | The product targets US users and the corpus is English |
