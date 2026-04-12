# EasyRAG

EasyRAG 是一个面向教学与工程实践的轻量级 RAG 核心库，聚焦于本地文档索引、混合检索与轻量知识图谱整理。  
EasyRAG is a lightweight RAG core library for teaching and practical engineering, focused on local document indexing, hybrid retrieval, and lightweight knowledge graph curation.

## 适合人群 / Who This Is For

- 想系统理解 RAG 基本链路的学习者 / Learners who want a clear view of the core RAG pipeline
- 需要一个小而清晰的 RAG 代码库来阅读与扩展的开发者 / Developers who prefer a small, readable codebase for study and extension
- 希望把“索引、检索、图谱、存储”拆开理解的教学场景 / Teaching scenarios that want to explain indexing, retrieval, graph, and storage separately

## 你将学到什么 / What You Will Learn

- 文档加载、切块、索引与查询的基本流程 / The end-to-end flow of loading, chunking, indexing, and querying
- 混合检索与重排的基本组织方式 / A compact structure for hybrid retrieval and reranking
- 轻量知识图谱如何参与 RAG / How lightweight knowledge graph curation can support RAG
- 本地存储与可替换后端的职责划分 / How local storage and swappable backends are separated

## 快速开始 / Quick Start

创建并激活虚拟环境：  
Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

安装核心包：  
Install the core package:

```bash
pip install -e .
```

如需测试依赖：  
Install test dependencies if needed:

```bash
pip install -e ".[dev]"
```

构建本地索引：  
Build the local index:

```bash
python scripts/build_index.py
```

## 学习路径 / Learning Path

### 文档主线 / Docs Mainline

1. 阅读 [项目概览 / Overview](docs/00-overview.md)
2. 了解 [RAG 基础 / RAG Basics](docs/01-rag-basics.md)
3. 继续看 [数据加载总览 / Data Loading Overview](docs/02-data-loading-overview.md)
4. 再看 [索引总览 / Indexing Overview](docs/03-indexing-overview.md)
5. 再看 [检索总览 / Retrieval Overview](docs/04-retrieval-overview.md)
6. 再进入 [生成总览 / Generation Overview](docs/05-generation-overview.md)
7. 接着读 [评估总览 / Evaluation Overview](docs/06-evaluation-overview.md)
8. 再看 [优化总览 / Optimization Overview](docs/07-optimization-overview.md)
9. 最后回到 [系统架构总览 / System Architecture Overview](docs/08-system-architecture-overview.md)

### 方法原理专题 / Principles

- [Query 预处理](docs/principles/10-query-preprocessing.md)
- [Chunk 分块策略](docs/principles/11-chunking-strategies.md)
- [向量 Index 原理](docs/principles/12-vector-index-principles.md)
- [混合检索与融合](docs/principles/13-hybrid-retrieval-and-fusion.md)
- [Reranking 与候选选择](docs/principles/14-reranking-and-selection.md)
- [知识图谱如何参与 RAG](docs/principles/15-knowledge-graph-for-rag.md)
- [存储后端与取舍](docs/principles/16-storage-backends-and-tradeoffs.md)
- [评估与调试](docs/principles/17-evaluation-and-debugging.md)
- [Generation 基础](docs/principles/18-generation-foundations.md)
- [Top-k 与候选选择](docs/principles/19-top-k-and-candidate-selection.md)
- [上下文组装与 Packing](docs/principles/20-context-assembly-and-packing.md)
- [Prompting 与答案合成](docs/principles/21-prompting-and-answer-synthesis.md)
- [Generation 失败模式与 Guardrails](docs/principles/22-generation-failures-and-guardrails.md)

### 工程实现专题 / Engineering

- [代码地图 / Code Map](docs/engineering/20-code-map.md)
- [索引 Pipeline](docs/engineering/21-indexing-pipeline.md)
- [检索 Pipeline](docs/engineering/22-retrieval-pipeline.md)
- [图谱整理 Pipeline](docs/engineering/23-graph-curation-pipeline.md)
- [本地与生产后端](docs/engineering/24-local-vs-production-backends.md)
- [扩展指南](docs/engineering/25-extension-guide.md)
- [Generation Pipeline](docs/engineering/26-generation-pipeline.md)

之后从 [Notebooks](notebooks/README.md) 和 [Examples](examples/README.md) 进入实践。

## 文档地图 / Documentation Map

- [docs/README.md](docs/README.md)：完整文档索引
- [notebooks/README.md](notebooks/README.md)：完整 notebook 索引

## 仓库结构 / Repository Layout

- [easyrag/](easyrag/)：核心库实现 / Core library implementation
- [scripts/](scripts/)：本地索引 CLI / Local indexing CLI
- [tests/](tests/)：现有测试集 / Existing test suite
- [docs/](docs/README.md)：教学文档目录与导航 / Teaching documentation map
- [notebooks/](notebooks/README.md)：教学 Notebook 目录与导航 / Teaching notebook map
- [examples/](examples/README.md)：示例脚本骨架 / Example script scaffold
- [sample_data/](sample_data/README.md)：示例数据骨架 / Sample data scaffold

## Notebooks

### Overview

- [00_quickstart.ipynb](notebooks/00_overview/00_quickstart.ipynb): 最小上手流程

### Data Loading

- [02_01_repo_loading.ipynb](notebooks/02_data_loading/02_01_repo_loading.ipynb): repo loading 与 canonical documents
- [02_02_custom_documents.ipynb](notebooks/02_data_loading/02_02_custom_documents.ipynb): 自定义文档接入

### Indexing

- [03_01_build_index.ipynb](notebooks/03_indexing/03_01_build_index.ipynb): 索引构建说明
- [03_02_chunking_strategy_lab.ipynb](notebooks/03_indexing/03_02_chunking_strategy_lab.ipynb): chunk 策略实验

### Retrieval

- [04_01_query_modes.ipynb](notebooks/04_retrieval/04_01_query_modes.ipynb): 查询模式对比
- [04_02_knowledge_graph.ipynb](notebooks/04_retrieval/04_02_knowledge_graph.ipynb): 知识图谱部分
- [04_03_query_preprocessing_lab.ipynb](notebooks/04_retrieval/04_03_query_preprocessing_lab.ipynb): query 预处理实验
- [04_04_vector_retrieval_lab.ipynb](notebooks/04_retrieval/04_04_vector_retrieval_lab.ipynb): 向量检索实验
- [04_05_hybrid_fusion_lab.ipynb](notebooks/04_retrieval/04_05_hybrid_fusion_lab.ipynb): 混合检索与融合实验
- [04_06_rerank_lab.ipynb](notebooks/04_retrieval/04_06_rerank_lab.ipynb): rerank 实验

### Generation

- [05_01_generation_basics.ipynb](notebooks/05_generation/05_01_generation_basics.ipynb): generation 基础路径
- [05_02_top_k_selection_lab.ipynb](notebooks/05_generation/05_02_top_k_selection_lab.ipynb): top-k 选择实验
- [05_03_context_packing_lab.ipynb](notebooks/05_generation/05_03_context_packing_lab.ipynb): 上下文组装实验
- [05_04_prompting_and_answer_style_lab.ipynb](notebooks/05_generation/05_04_prompting_and_answer_style_lab.ipynb): prompt 与回答风格实验
- [05_05_generation_failure_cases.ipynb](notebooks/05_generation/05_05_generation_failure_cases.ipynb): generation 失败案例实验

### Evaluation

- [06_01_eval_basics.ipynb](notebooks/06_evaluation/06_01_eval_basics.ipynb): 评估对象与分层
- [06_02_build_tiny_eval_set.ipynb](notebooks/06_evaluation/06_02_build_tiny_eval_set.ipynb): 小型评测集构造
- [06_03_retrieval_metrics.ipynb](notebooks/06_evaluation/06_03_retrieval_metrics.ipynb): retrieval metrics
- [06_04_grounding_and_faithfulness.ipynb](notebooks/06_evaluation/06_04_grounding_and_faithfulness.ipynb): grounding 与 faithfulness
- [06_05_eval_driven_debugging.ipynb](notebooks/06_evaluation/06_05_eval_driven_debugging.ipynb): 评估驱动调试

### System Architecture

- [08_01_storage_backend_lab.ipynb](notebooks/08_system_architecture/08_01_storage_backend_lab.ipynb): backend 对比实验

`Optimization` 目前只提供 docs overview，不提供 notebook 目录。

## Examples

- [quickstart.py](examples/quickstart.py): 最小脚本示例占位 / Placeholder for a minimal script example
- [build_index_demo.py](examples/build_index_demo.py): 索引脚本示例占位 / Placeholder for index-building demo
- [query_demo.py](examples/query_demo.py): 查询脚本示例占位 / Placeholder for query demo

## Development

运行当前核心测试集：  
Run the current focused test suite:

```bash
python -m pytest -q tests/test_config.py tests/test_rag_providers.py tests/test_rag_retriever.py tests/test_rag_graph_ops.py tests/test_rag_backends.py
```

更多教学内容会优先放在 `docs/`、`notebooks/` 与 `examples/` 中，避免影响核心库接口。  
Future teaching material should live in `docs/`, `notebooks/`, and `examples/` without changing the core library interface.

## Roadmap

- 补全 evaluation notebooks 的实作内容 / Flesh out the evaluation notebook bodies
- 从评估结果反推 optimization notebooks / Grow optimization material from real evaluation loops
- 补全示例脚本 / Add runnable example scripts
- 补充练习与教学数据 / Add exercises and sample data
