# Docs

Mainline: 按阶段学习
Principles: 按方法学习
Engineering: 按代码实现学习

EasyRAG 的文档按学习主线组织，并辅以原理专题与工程专题。

当前状态：

- `overview` 只讲阶段心智模型、输入输出与学习路径。
- `principles` 只讲通用方法，不绑定仓库文件路径，不重复 notebook 导航。
- `engineering` 只讲实现落点、模块关系与扩展点，不重复大段方法论。
- `principles` 和 `engineering` 下的大部分页面目前仍是 `draft/placeholder`，但已统一为同一模板，方便后续补正文。

## 主线文档 / Mainline

- [00-overview.md](00-overview.md): 项目总览与学习入口
- [01-rag-basics.md](01-rag-basics.md): RAG 基础概念与核心对象，docs-only
- [02-data-loading-overview.md](02-data-loading-overview.md): 输入进入系统之前的加载与规范化
- [03-indexing-overview.md](03-indexing-overview.md): 索引阶段总览
- [04-retrieval-overview.md](04-retrieval-overview.md): 检索阶段总览
- [05-generation-overview.md](05-generation-overview.md): generation 阶段总览
- [06-evaluation-overview.md](06-evaluation-overview.md): 评估与定位问题
- [07-optimization-overview.md](07-optimization-overview.md): 优化路线图，当前为 docs-only
- [08-system-architecture-overview.md](08-system-architecture-overview.md): 全局架构回看

说明：

- `01-rag-basics` 继续作为 docs-only 基础词汇页
- `07-optimization-overview` 继续作为 docs-only 路线图
- `06-evaluation-overview` 已是主线的一部分，不再只是补充章节
- 多个 overview 已显式纳入工业界常用方法，如 normalization、metadata filtering、hybrid retrieval、rerank、latency/cost、fallback

## 方法原理专题 / Principles

- [10-query-preprocessing.md](principles/10-query-preprocessing.md)
- [11-chunking-strategies.md](principles/11-chunking-strategies.md)
- [12-vector-index-principles.md](principles/12-vector-index-principles.md)
- [13-hybrid-retrieval-and-fusion.md](principles/13-hybrid-retrieval-and-fusion.md)
- [14-reranking-and-selection.md](principles/14-reranking-and-selection.md)
- [15-knowledge-graph-for-rag.md](principles/15-knowledge-graph-for-rag.md)
- [16-storage-backends-and-tradeoffs.md](principles/16-storage-backends-and-tradeoffs.md)
- [17-top-k-and-candidate-selection.md](principles/17-top-k-and-candidate-selection.md)
- [18-context-assembly-and-packing.md](principles/18-context-assembly-and-packing.md)
- [19-prompting-and-answer-synthesis.md](principles/19-prompting-and-answer-synthesis.md)
- [20-generation-failures-and-guardrails.md](principles/20-generation-failures-and-guardrails.md)
- [21-evaluation-and-debugging.md](principles/21-evaluation-and-debugging.md)

说明：

- `principles` 按“从输入到答案，再到评估优化”的顺序排布。
- generation 相关主题连续出现，evaluation 放在最后，避免阅读路径来回跳。

## 工程实现专题 / Engineering

- [20-code-map.md](engineering/20-code-map.md)
- [21-indexing-pipeline.md](engineering/21-indexing-pipeline.md)
- [22-retrieval-pipeline.md](engineering/22-retrieval-pipeline.md)
- [23-generation-pipeline.md](engineering/23-generation-pipeline.md)
- [24-graph-curation-pipeline.md](engineering/24-graph-curation-pipeline.md)
- [25-local-vs-production-backends.md](engineering/25-local-vs-production-backends.md)
- [26-extension-guide.md](engineering/26-extension-guide.md)

说明：

- `engineering` 先给代码总览，再按运行链路，再讲系统边界，最后讲扩展。
- [20-code-map.md](engineering/20-code-map.md) 是工程专题的首要入口，后续内容默认从这里跳转。

## 教学锚点 / Teaching Anchors

Current interfaces:

- `EasyRAG`
- `QueryParam`
- `ChunkingConfig`
- `QueryResult`

Downstream generation and answer-shaping work remains notebook- and docs-led for now rather than a built-in public API.
