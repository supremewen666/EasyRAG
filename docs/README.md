# Docs

EasyRAG 的文档分成三层：

- 主线文档：先建立稳定心智模型
- 方法原理专题：再拆开讲 query、chunk、向量索引、fusion、KG 等原理
- 工程实现专题：最后回到代码结构、pipeline 和扩展点

## 项目入口 / Entry Points

- [00-overview.md](00-overview.md): 项目总览与学习入口
- [01-rag-basics.md](01-rag-basics.md): RAG 基础概念与核心对象
- [02-system-architecture.md](02-system-architecture.md): 系统级数据流与模块边界
- [03-indexing-overview.md](03-indexing-overview.md): 索引阶段总览
- [04-retrieval-overview.md](04-retrieval-overview.md): 检索阶段总览
- [05-generation-overview.md](05-generation-overview.md): 生成阶段总览

## 方法原理专题 / Principles

- [10-query-preprocessing.md](principles/10-query-preprocessing.md)
- [11-chunking-strategies.md](principles/11-chunking-strategies.md)
- [12-vector-index-principles.md](principles/12-vector-index-principles.md)
- [13-hybrid-retrieval-and-fusion.md](principles/13-hybrid-retrieval-and-fusion.md)
- [14-reranking-and-selection.md](principles/14-reranking-and-selection.md)
- [15-knowledge-graph-for-rag.md](principles/15-knowledge-graph-for-rag.md)
- [16-storage-backends-and-tradeoffs.md](principles/16-storage-backends-and-tradeoffs.md)
- [17-evaluation-and-debugging.md](principles/17-evaluation-and-debugging.md)
- [18-generation-foundations.md](principles/18-generation-foundations.md)
- [19-top-k-and-candidate-selection.md](principles/19-top-k-and-candidate-selection.md)
- [20-context-assembly-and-packing.md](principles/20-context-assembly-and-packing.md)
- [21-prompting-and-answer-synthesis.md](principles/21-prompting-and-answer-synthesis.md)
- [22-generation-failures-and-guardrails.md](principles/22-generation-failures-and-guardrails.md)

## 工程实现专题 / Engineering

- [20-code-map.md](engineering/20-code-map.md)
- [21-indexing-pipeline.md](engineering/21-indexing-pipeline.md)
- [22-retrieval-pipeline.md](engineering/22-retrieval-pipeline.md)
- [23-graph-curation-pipeline.md](engineering/23-graph-curation-pipeline.md)
- [24-local-vs-production-backends.md](engineering/24-local-vs-production-backends.md)
- [25-extension-guide.md](engineering/25-extension-guide.md)
- [26-generation-pipeline.md](engineering/26-generation-pipeline.md)

## 教学锚点 / Teaching Anchors

## 教学锚点 / Teaching Anchors

Current interfaces:

- `EasyRAG`
- `QueryParam`
- `ChunkingConfig`
- `QueryResult.metadata`

Planned generation interfaces:

- `AnswerParam`
- `AnswerResult`
- `ContextAssemblyConfig`
- `PromptBuilder` / `PromptTemplate`
