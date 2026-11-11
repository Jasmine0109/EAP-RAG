# 欢迎使用 rag 工作区

这是一个本地 RAG（检索增强生成）的骨架项目。它把文档变成可检索的索引，
提问时先搜出相关片段，再把片段和问题一起交给 LLM。

## 数据流

1. ingest：读取 data/raw 下的 Markdown 和纯文本文件。
2. chunk：按空行分段，把段落拼成不超过 800 字的块，块之间尽量保留 120 字重叠。
3. embed：默认用哈希嵌入，离线、确定、零依赖；换成真模型是第一步升级。
4. store：正文和向量一起写进 data/index/index.sqlite3。
5. retrieve：提问时做余弦相似度暴力检索，取回最相关的 top-k 块。
6. generate：把片段和问题拼成 prompt，交给本地 Qwen 的 OpenAI 兼容接口。

## 常用命令

make ingest 建立索引，make ask Q="你的问题" 提问，make test 跑单元测试。
加上 --offline 参数可以跳过 LLM，只查看检索到的原文片段。

## 约定

data/raw 是唯一的事实来源，索引文件可以随时删除重建。
data/raw 里放了这篇示例文档，换成你自己的资料即可。
