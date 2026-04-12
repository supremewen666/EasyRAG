# EasyRAG 文档与 Notebook 重构方案

## Summary

主线继续采用“少量 overview + 每个 overview 下细分 notebooks”的结构，并在现有方案基础上补齐三类此前不足的内容：

1. `评估方法`：需要独立 `overview`，也需要对应 `notebooks`
2. `优化策略`：需要独立 `overview`，先作为待完成内容
3. `工业界常用方法`：要系统纳入各 overview 与 notebooks，而不是零散出现；其中必须显式补入“归一化”

重构后的教学主线建议扩展为 8 个 overview：

1. `00-overview`
2. `01-rag-basics`
3. `02-data-loading-overview`
4. `03-indexing-overview`
5. `04-retrieval-overview`
6. `05-generation-overview`
7. `06-evaluation-overview`
8. `07-optimization-overview`
9. `08-system-architecture-overview`

其中 `03-indexing-overview` 内部继续保持标准顺序：

`Document -> Chunk -> Embedding -> Vector Index -> Storage / Derived Artifacts`

并在 `02/03/04/05/06/07` 各层系统性加入工业界常用方法：归一化、去重、元数据过滤、混合检索、rerank、query rewrite、multi-query、cache、阈值控制、回退策略、离线评测、线上观测等。

## Overview Changes

### 1. `02-data-loading-overview`
这一章负责输入建模，并加入工业界常用的预处理方法。

建议内容：
- repo loading
- manual documents
- PDF / multimodal loading
- canonical `Document`
- metadata 规范与边界条件
- 文本清洗与预处理
- 新增 `normalization` 小节
  - Unicode 归一化
  - 空白归一化
  - 换行与段落归一化
  - 大小写策略
  - 标点统一
  - 路径与标题规范化
- 工业界常用方法补充
  - boilerplate removal
  - 模板内容剔除
  - 去重与 near-duplicate detection
  - 文档版本控制与更新时间 metadata
  - PII / 敏感字段处理
  - metadata enrichment

这一章的核心信息是：
归一化不是 retrieval 的附属技巧，而是数据进入系统后的第一层质量保障。

### 2. `03-indexing-overview`
这一章负责索引阶段的完整心智模型，并加入工业界更常见的 indexing 方法。

内部顺序固定为：
- chunking
- embedding
- vector index
- summaries
- graph enrichment
- storage writes
- workspace artifacts

新增必须覆盖的工业界常用方法：
- chunk normalization 与清洗后再切块
- overlap 策略
- parent-child chunking
- heading-aware chunking
- semantic chunking
- small-to-big retrieval 的索引准备
- embedding model selection
- embedding batching
- embedding cache
- 重建索引与增量索引
- 向量索引参数与 ANN 基础
- metadata filter-ready indexing
- hybrid-ready indexing
- title / summary / body 多字段索引
- 多 namespace 设计：`chunk`、`summary`、`entity`、`relation`

尤其要新增两个显式小节：

`Normalization Before Embedding`
- 说明为什么 embedding 前要做清洗与归一化
- 不同归一化策略会怎样影响向量一致性

`Industry Patterns In Indexing`
- parent-child
- multi-representation indexing
- summary indexing
- metadata-first filtering
- incremental indexing
- embedding cache

### 3. `04-retrieval-overview`
这一章要从“功能说明”升级成“工业界检索策略总览”。

建议内容：
- query preprocessing
- normalization
- query rewrite
- multi-query expansion
- metadata filter
- retrieval modes
- fusion
- rerank
- hydration
- citations
- diagnostics

必须新增 `Query Normalization` 小节：
- query 清洗
- 同义改写
- 缩写展开
- 时间、数字、单位标准化
- 中英混输与术语统一
- typo-tolerant thinking 的边界

必须系统纳入的工业界常用方法：
- lexical + dense hybrid retrieval
- metadata filtering
- field-aware retrieval
- rerank after recall
- top-k / score threshold 联合控制
- query decomposition
- self-query / structured filtering
- fallback retrieval path
- cache
- “查不到时怎么办”的 graceful degradation

这一章的目标是让读者看到：
工业界 retrieval 的关键不是某一个 mode，而是“预处理 + 召回 + 融合 + 精排 + 回退”的组合策略。

### 4. `05-generation-overview`
这一章加入工业界更常见的回答构造方法。

建议内容：
- `QueryResult` handoff
- evidence selection
- context packing
- prompting
- answer synthesis
- generation failures

新增工业界常用方法：
- citation-aware answering
- extractive-first synthesis
- answer template control
- refusal / insufficient evidence policy
- context truncation policy
- section-aware packing
- source diversification
- response grounding checks
- structured output
- answer post-processing normalization

新增 `Industrial Answering Patterns` 小节：
- answer with citations
- answer only from provided context
- abstain on weak evidence
- structured answers for downstream systems
- reference-preserving summarization

### 5. 新增 `06-evaluation-overview`
这是完整新增章节，内容需更偏工程与工业实践。

建议内容：
- 为什么 RAG 需要评估
- 分层评估：
  - corpus quality
  - chunk quality
  - retrieval quality
  - rerank quality
  - answer quality
  - end-to-end task quality
- 常见指标：
  - recall@k
  - precision@k
  - hit rate
  - MRR / NDCG
  - grounding / faithfulness
  - answer usefulness
  - latency
  - cost
- 构造 eval set
- 离线评测 vs 在线评测
- A/B testing 与 shadow evaluation
- 失败类型分类
- eval-driven debugging

必须新增 `Industrial Evaluation Methods` 小节：
- golden set
- synthetic eval set
- pairwise answer comparison
- citation verification
- human-in-the-loop review
- latency / throughput SLO
- cost-per-query analysis
- regression suite

### 6. 新增 `07-optimization-overview`
这一章作为待完成内容，但要比占位更完整，明确工业界常用优化方向。

建议内容：
- 优化前提：先评估再优化
- 优化层次：
  - data normalization / cleaning
  - chunk strategy tuning
  - embedding model choice
  - vector index parameter tuning
  - hybrid recall design
  - rerank policy
  - prompt / packing policy
  - cache / latency / cost tradeoff
- 新增 `Industrial Optimization Patterns` 小节
  - normalization tuning
  - metadata filter refinement
  - ANN parameter tuning
  - score calibration
  - rerank depth tuning
  - query rewrite policy tuning
  - adaptive top-k
  - cache hit strategy
  - multi-stage retrieval
  - domain lexicon injection
- 明确标注：
  - 本章先提供框架与优化地图
  - notebook 后续补充

### 7. `08-system-architecture-overview`
这一章保留为回看全局，但应补入工业实践的系统组件视角：

- orchestrator
- local vs production bundles
- ingestion pipeline
- retrieval pipeline
- evaluation pipeline
- cache / logging / observability
- extension points

新增 `Production Concerns` 小节：
- observability
- tracing
- caching
- retry / timeout
- fallback
- multi-backend deployment

## Notebook Structure

建议目录改成：

- `notebooks/00_overview/`
- `notebooks/02_data_loading/`
- `notebooks/03_indexing/`
- `notebooks/04_retrieval/`
- `notebooks/05_generation/`
- `notebooks/06_evaluation/`
- `notebooks/08_system_architecture/`

`07_optimization` 本轮仍不建 notebook，只保留 overview。

## Notebook Breakdown

### `00_overview/`
- `00_01_quickstart_end_to_end.ipynb`
- `00_02_observing_rag_artifacts.ipynb`

### `02_data_loading/`
建议扩充为 5 个 notebook：

- `02_01_repo_loading_basics.ipynb`
- `02_02_manual_document_preparation.ipynb`
- `02_03_pdf_and_multimodal_loading.ipynb`
- `02_04_normalization_and_cleaning.ipynb`
- `02_05_document_quality_and_edge_cases.ipynb`

新增重点本：
`02_04_normalization_and_cleaning.ipynb`
- 文本归一化前后对比
- 标题、路径、空白、标点、编码问题
- 重复内容与模板噪声
- 说明这些处理如何影响 chunking 和 retrieval

### `03_indexing/`
建议扩充为 8 个 notebook：

- `03_01_chunking_principles.ipynb`
- `03_02_chunking_quality_analysis.ipynb`
- `03_03_embeddings_basics.ipynb`
- `03_04_normalization_before_embedding.ipynb`
- `03_05_embedding_inputs_and_provider_behavior.ipynb`
- `03_06_vector_index_basics.ipynb`
- `03_07_build_index_pipeline.ipynb`
- `03_08_storage_and_workspace_artifacts.ipynb`

新增重点本：
`03_04_normalization_before_embedding.ipynb`
- 为什么 embedding 前需要清洗与归一化
- 不同 normalization 策略对 embedding 相似度的影响
- 示例对比：脏文本 vs 归一化文本

`03_06_vector_index_basics.ipynb`
- 继续保证“向量索引放在 embedding 之后”
- 补充工业界常用内容：
  - ANN 基本直觉
  - namespace 设计
  - metadata-aware indexing
  - incremental indexing

### `04_retrieval/`
建议扩充为 7 个 notebook：

- `04_01_query_normalization_and_preprocessing.ipynb`
- `04_02_query_rewrite_and_multi_query.ipynb`
- `04_03_naive_retrieval_basics.ipynb`
- `04_04_hybrid_metadata_filter_and_modes.ipynb`
- `04_05_fusion_rerank_and_topk.ipynb`
- `04_06_hydration_and_citations.ipynb`
- `04_07_retrieval_failure_cases_and_debugging.ipynb`

新增重点：
`04_01_query_normalization_and_preprocessing.ipynb`
- 显式讲 query normalization
- 归一化、术语统一、缩写处理、数字和单位规范化

`04_04_hybrid_metadata_filter_and_modes.ipynb`
- 把工业界常用的 hybrid retrieval 和 metadata filter 正式纳入主线

### `05_generation/`
建议保留 5 个 notebook，并补入工业界方法：

- `05_01_query_result_to_answer.ipynb`
- `05_02_evidence_selection_and_topk_for_answering.ipynb`
- `05_03_context_assembly_and_packing.ipynb`
- `05_04_prompting_and_answer_style.ipynb`
- `05_05_generation_failures_and_guardrails.ipynb`

每本内部应补入：
- abstention policy
- citation-aware output
- structured output
- insufficient evidence handling

### `06_evaluation/`
继续保留完整评估组，并补入更工业化的方法：

- `06_01_evaluation_basics.ipynb`
- `06_02_building_a_tiny_eval_set.ipynb`
- `06_03_retrieval_metrics.ipynb`
- `06_04_answer_grounding_and_faithfulness.ipynb`
- `06_05_eval_driven_debugging.ipynb`
- 新增 `06_06_latency_cost_and_regression_checks.ipynb`

新增重点本：
`06_06_latency_cost_and_regression_checks.ipynb`
- latency / throughput
- cost tracking
- regression suite
- release 前后评测对比

### `08_system_architecture/`
- `08_01_code_map_and_runtime_flow.ipynb`
- `08_02_local_vs_production_backends.ipynb`
- 可新增 `08_03_observability_and_fallbacks.ipynb`

## Content Design Rules

### 1. 每个 overview 都要显式覆盖“工业界常用方法”

不能只在文中顺带提，要有明确的小节标题或 notebook 标题。  
特别是以下内容必须显式出现：

- normalization
- deduplication
- metadata filtering
- hybrid retrieval
- reranking
- caching
- fallback
- thresholding
- regression evaluation
- latency / cost tracking

### 2. `normalization` 必须成为横向贯穿概念

需要在 4 个地方都出现：
- `02-data-loading-overview`
- `03-indexing-overview`
- `04-retrieval-overview`
- 对应 notebook：`02_04`、`03_04`、`04_01`

它的定位不是小技巧，而是贯穿输入质量、embedding 一致性、query 匹配性的基础方法。

### 3. 每个 notebook 保持“概念 -> 例子 -> 对比 -> 失败模式/边界”

尤其对工业方法类 notebook，要避免只列方法名。  
需要做到：
- 有中间对象
- 有前后对比
- 有失败案例
- 能解释为什么工业界会用这类方法

### 4. `optimization` 虽然暂不做 notebook，但 overview 要足够可执行

这一章要写到“后续 notebook 会按什么层次展开”，至少包括：
- data normalization tuning
- chunk tuning
- embedding/index tuning
- retrieval tuning
- prompt tuning
- latency/cost tuning

## README Alignment

以下 3 个入口要统一更新，并显式加入“评估方法”“优化策略”“工业界常用方法”的说明：

- [README.md](/Users/supremewen/EasyRAG/README.md)
- [docs/README.md](/Users/supremewen/EasyRAG/docs/README.md)
- [notebooks/README.md](/Users/supremewen/EasyRAG/notebooks/README.md)

在导航说明里明确：
- `Evaluation` 有完整 notebook 配套
- `Optimization` 目前为待完成 overview
- 多个 overview 已系统纳入工业界常用方法，而不再只讲教学最小闭环

## Test Plan

- 检查 docs 主线是否已经包含：
  - `06-evaluation-overview`
  - `07-optimization-overview`
- 检查 `normalization` 是否在 data loading、indexing、retrieval 三个 overview 中都有显式小节。
- 检查以下 notebook 是否存在并定位明确：
  - `02_04_normalization_and_cleaning.ipynb`
  - `03_04_normalization_before_embedding.ipynb`
  - `04_01_query_normalization_and_preprocessing.ipynb`
- 检查 `03-indexing-overview` 与 `03_indexing/` 下 notebook 顺序是否仍满足：
  `chunking -> embedding -> vector index`
- 检查 retrieval 层是否显式覆盖：
  - hybrid retrieval
  - metadata filter
  - rerank
  - fallback
- 检查 evaluation 层是否显式覆盖：
  - offline metrics
  - grounding
  - latency/cost
  - regression checks
- 检查 `07-optimization-overview` 是否包含工业界常见优化地图，而不是只有占位说明。
- 检查所有 README 导航是否同步加入新增内容，并与 docs/notebooks 结构一致。

## Assumptions

- 评估方法是本轮必须新增的完整板块。
- 优化策略仍然先保留为 overview，不要求本轮 notebook 落地。
- 工业界常用方法需要贯穿多个 overview，而不是集中成一个杂项章节。
- `normalization` 是本轮新增中的硬要求，必须作为显式主题进入 docs 与 notebooks。
- 主线仍然追求 overview 少而清楚，不会因为新增工业方法而重新碎片化主线文件。
