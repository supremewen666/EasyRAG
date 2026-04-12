# EasyRAG 文档与 Notebook 重构方案

## Summary

主线继续采用“少量 overview + 每个 overview 下细分 notebooks”的结构，并在现有方案上补入两块新内容：

1. `评估方法`：需要独立 `overview`，也需要对应 `notebooks`
2. `优化策略`：需要独立 `overview`，但先作为待完成内容，不要求这轮配套 notebook

重构后的教学主线建议扩展为 8 个 overview：

1. `00-overview`
2. `01-rag-basics`
3. `02-data-loading-overview`
4. `03-indexing-overview`
5. `04-retrieval-overview`
6. `05-generation-overview`
7. 新增 `06-evaluation-overview`
8. 新增 `07-optimization-overview`
9. `08-system-architecture-overview`

其中 `03-indexing-overview` 内部继续保持：
`Document -> Chunk -> Embedding -> Vector Index -> Storage / Derived Artifacts`

## Overview Changes

### 1. `02-data-loading-overview`
内容不变，负责输入建模：
- repo loading
- manual documents
- PDF / multimodal loading
- canonical `Document`
- metadata 规范与边界条件

### 2. `03-indexing-overview`
内容不变，但明确内部顺序：
- chunking
- embedding
- vector index
- summaries
- graph enrichment
- storage writes
- workspace artifacts

### 3. `04-retrieval-overview`
内容不变：
- query preprocessing
- retrieval modes
- fusion
- rerank
- hydration
- citations
- diagnostics

### 4. `05-generation-overview`
内容不变：
- `QueryResult` handoff
- evidence selection
- context packing
- prompting
- answer synthesis
- generation failures

### 5. 新增 `06-evaluation-overview`
这是必须新增的完整主线章节。

建议包含：
- 为什么 RAG 需要评估，而不是只看“回答看起来不错”
- 评估对象分层：
  - data loading / corpus quality
  - chunking quality
  - retrieval quality
  - answer quality
  - end-to-end task success
- 常见评估维度：
  - recall
  - precision
  - hit rate
  - MRR / ranking quality
  - citation grounding
  - answer faithfulness
  - answer usefulness
  - latency / cost
- 离线评估 vs 在线评估
- 小样本教学评估集如何构造
- EasyRAG 里哪些中间对象可以直接用于评估：
  - chunks
  - citations
  - retrieval metadata
  - `QueryResult`
- 调试与评估的关系：评估不是最终汇报，而是定位问题的工具

这一章的定位是：
把当前散落在 `17-evaluation-and-debugging`、retrieval failure cases、generation failures 里的评估意识正式前置成独立主线。

### 6. 新增 `07-optimization-overview`
这是“只要 overview，作为待完成内容”的章节。

建议只定义框架，不要求本轮写完整 notebook。

建议包含：
- 优化发生在哪些层：
  - data quality
  - chunking strategy
  - embedding model choice
  - vector backend / indexing parameters
  - retrieval mode selection
  - rerank policy
  - context packing
  - prompting policy
- 优化目标有哪些：
  - recall 提升
  - precision 提升
  - grounding 提升
  - latency 降低
  - 成本降低
  - 稳定性提升
- 优化方法的组织方式：
  - 先评估，再定位，再优化
  - 避免“感觉调参”
- 当前状态说明：
  - 本章作为待完成内容
  - 后续会根据评估体系补充更系统的方法和案例

这一章应明确标注：
- 这是 roadmap 型 overview
- 本轮先给框架，不要求深入实现或 notebook 对齐

### 7. `08-system-architecture-overview`
后移为全局回看：
- orchestrator
- indexing / retrieval / generation 边界
- local vs production bundles
- extension points

## Notebook Structure

建议目录改成：

- `notebooks/00_overview/`
- `notebooks/02_data_loading/`
- `notebooks/03_indexing/`
- `notebooks/04_retrieval/`
- `notebooks/05_generation/`
- 新增 `notebooks/06_evaluation/`
- `notebooks/08_system_architecture/`

`07_optimization` 本轮不建 notebook，只在 docs 中作为待完成 overview 保留。

## Notebook Breakdown

### `00_overview/`
- `00_01_quickstart_end_to_end.ipynb`
- `00_02_observing_rag_artifacts.ipynb`

### `02_data_loading/`
- `02_01_repo_loading_basics.ipynb`
- `02_02_manual_document_preparation.ipynb`
- `02_03_pdf_and_multimodal_loading.ipynb`
- `02_04_document_quality_and_edge_cases.ipynb`

### `03_indexing/`
- `03_01_chunking_principles.ipynb`
- `03_02_chunking_quality_analysis.ipynb`
- `03_03_embeddings_basics.ipynb`
- `03_04_embedding_inputs_and_provider_behavior.ipynb`
- `03_05_vector_index_basics.ipynb`
- `03_06_build_index_pipeline.ipynb`
- `03_07_storage_and_workspace_artifacts.ipynb`

### `04_retrieval/`
- `04_01_query_preprocessing.ipynb`
- `04_02_naive_retrieval_basics.ipynb`
- `04_03_local_global_hybrid_modes.ipynb`
- `04_04_fusion_rerank_and_topk.ipynb`
- `04_05_hydration_and_citations.ipynb`
- `04_06_retrieval_failure_cases_and_debugging.ipynb`

### `05_generation/`
- `05_01_query_result_to_answer.ipynb`
- `05_02_evidence_selection_and_topk_for_answering.ipynb`
- `05_03_context_assembly_and_packing.ipynb`
- `05_04_prompting_and_answer_style.ipynb`
- `05_05_generation_failures_and_guardrails.ipynb`

### 新增 `06_evaluation/`
这一组 notebook 必须补上，用来承接 `06-evaluation-overview`。

建议至少 5 个 notebook：

- `06_01_evaluation_basics.ipynb`
  - 评估对象分层
  - retrieval eval 与 answer eval 的区别
  - 最小评估数据结构示例

- `06_02_building_a_tiny_eval_set.ipynb`
  - 如何构造教学用 query / gold evidence / expected answer
  - 如何从现有 docs 语料中人工做小型评测集
  - 为什么教学项目需要可解释的小样本 benchmark

- `06_03_retrieval_metrics.ipynb`
  - hit rate
  - recall@k
  - precision@k
  - MRR
  - candidate coverage
  - 用真实 `QueryResult.citations` 做指标计算

- `06_04_answer_grounding_and_faithfulness.ipynb`
  - answer 是否被 citation 支撑
  - answer usefulness 与 faithfulness 的区别
  - retrieval 对但 answer 错、answer 对但 citation 弱 的案例

- `06_05_eval_driven_debugging.ipynb`
  - 如何根据评估结果回溯到 loading / chunking / embedding / retrieval / prompting 哪一层
  - 评估和 failure case notebook 联动
  - 建立“先测量，再优化”的教学闭环

这组 notebook 的目标是：
让读者不仅会跑系统，还知道如何判断系统“哪里好、哪里坏、坏在哪层”。

### `08_system_architecture/`
- `08_01_code_map_and_runtime_flow.ipynb`
- `08_02_local_vs_production_backends.ipynb`

## Content Design Rules

### 1. 每个 overview 下的 notebooks 采用固定节奏

统一节奏建议为：
- 第 1 本：概念与最小对象
- 第 2-3 本：策略 / 差异 / 中间产物
- 最后 1 本：失败模式或调试
- 对 `evaluation` 额外增加“指标与评测集构造”本

### 2. `evaluation` 必须成为横向总线

评估不是独立孤岛，应在各 overview 中都有回链：
- data loading notebook 结尾指出如何评估输入质量
- indexing notebook 结尾指出如何评估 chunk / embedding / index
- retrieval notebook 结尾指出如何进入 retrieval eval
- generation notebook 结尾指出如何进入 grounding eval

### 3. `optimization` 先作为框架章节，不展开 notebook

`07-optimization-overview` 要明确写成：
- 依赖评估结果的下一阶段工作
- 当前仓库中可优化的层有哪些
- 后续 notebook 将如何补齐

它的存在意义是：
先把“评估之后怎么办”在教学路径里占位，避免主线停在诊断而没有改进方向。

## README Alignment

以下 3 个入口要统一更新，并显式加入 `Evaluation` 和 `Optimization`：

- [README.md](/Users/supremewen/EasyRAG/README.md)
- [docs/README.md](/Users/supremewen/EasyRAG/docs/README.md)
- [notebooks/README.md](/Users/supremewen/EasyRAG/notebooks/README.md)

推荐展示顺序：

- Overview
- RAG Basics
- Data Loading Overview
- Indexing Overview
- Retrieval Overview
- Generation Overview
- Evaluation Overview
- Optimization Overview
- System Architecture Overview

并在 `notebooks/README.md` 中明确说明：
- `Evaluation` 有完整 notebook 配套
- `Optimization` 暂为待完成内容，当前只提供 docs overview

## Test Plan

- 检查 docs 主线是否已经包含：
  - `06-evaluation-overview`
  - `07-optimization-overview`
- 检查 `notebooks/06_evaluation/` 是否存在，并至少覆盖：
  - eval basics
  - eval set construction
  - retrieval metrics
  - grounding / faithfulness
  - eval-driven debugging
- 检查 `07-optimization-overview` 是否只作为 overview 存在，并明确标注待完成状态。
- 检查所有 README 导航是否同步加入 Evaluation 与 Optimization。
- 检查 `03-indexing-overview` 内部是否仍保持：
  `chunking -> embedding -> vector index`
- 检查 `evaluation` 是否与 retrieval / generation notebooks 建立回链，而不是孤立章节。
- 检查新手能否沿着主线形成完整闭环：
  `构建 -> 检索 -> 生成 -> 评估 -> 再考虑优化`

## Assumptions

- 评估方法是本轮必须新增的完整教学板块，既要 overview，也要 notebook。
- 优化策略是本轮必须占位的主线章节，但先不要求 notebook 与完整实现。
- `Optimization` 的逻辑前提是 `Evaluation` 已成立，因此顺序固定为先评估、后优化。
- 主线依然追求“overview 少而清楚”，不会为了新增内容重新打散成过多主线文件。
