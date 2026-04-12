# EasyRAG

![logo](./new_logo.png)

EasyRAG 是一个面向教学与工程实践的轻量级 RAG 学习项目。它把一个小型 RAG 系统拆成清晰可见的阶段: 数据加载、索引、检索、生成、评估、优化与系统架构，并用 `docs/`、Jupyter notebooks 和一套可阅读的核心代码，把这些阶段逐步展开。

如果你希望学到的不只是“调用一个黑盒 RAG API”，而是看清楚中间对象、关键取舍和代码落点，这个仓库就是为此设计的。

## 项目特点

- 教学优先: 内容按 pipeline 顺序组织，适合从零理解 RAG 的完整链路。
- 中间产物可观察: `Document`、chunk、summary、vector、graph state、citation、`QueryResult` 都尽量保持可检查。
- 文档与实验镜像: `docs/` 讲概念和阶段心智模型，`notebooks/` 用可运行或半骨架实验对应同一主题。
- 代码体量小而清晰: 核心入口集中在 `EasyRAG`、`QueryParam`、`ChunkingConfig`、`QueryResult` 等少数对象上。
- 兼顾本地与工程扩展: 默认是本地优先的教学实现，同时保留 swappable backends、provider hooks 和知识图谱整理能力。
- 支持零密钥起步: 部分 notebook 提供 deterministic stub 或 fallback 路径，先学结构，再接真实模型。

## 适合谁

- 想系统理解 RAG 基本链路的学习者
- 想找一个比“大而全框架”更容易读透的 RAG 代码库的开发者
- 希望把课程、实验和代码仓库统一起来的教学者
- 想围绕 chunking、hybrid retrieval、rerank、grounding、eval 等主题做专题讲解的人

## 你会学到什么

- 原始资料如何变成 canonical `Document`
- chunking、embedding、vector index、graph curation 如何组成索引阶段
- query normalization、rewrite、multi-query、fusion、rerank、hydration 如何构成检索阶段
- retrieval result 如何交给 answer generation、prompting 与 guardrails
- 为什么 evaluation 应该是主线的一部分，而不是附录
- 本地后端、生产后端、可观测性与 fallback 应该怎样纳入同一个系统心智模型

## 这不是一个什么项目

- 它不是“一键上线”的完整生产 RAG 平台
- 它不是依赖隐藏在框架内部的大而全封装
- 它也不是只给你一堆 notebook 而没有工程代码落点的课程仓库

EasyRAG 更像是一个可教学、可拆解、可扩展的小型 RAG 样本工程。

## 当前内容状态

- `docs/` 主线结构已经稳定，适合顺序阅读
- `notebooks/` 编号和叙事顺序已经稳定，但不同 notebook 的完成度不完全一致
- `scripts/build_index.py` 已可作为真实索引构建入口使用
- `examples/` 当前仍以占位脚本为主，主要实践入口仍在 notebooks
- `01-rag-basics` 与 `07-optimization-overview` 当前是 docs-only 章节

这意味着: 仓库已经很适合“按图索骥地学”和“顺着代码读”，但仍在持续补齐更深的实验内容。

## 快速开始

### 1. 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

如需开发依赖:

```bash
pip install -e ".[dev]"
```

可选后端依赖:

```bash
pip install -e ".[hnsw]"
pip install -e ".[postgres]"
```

项目当前要求 Python `>=3.11`。

### 2. 最推荐的第一个入口

如果你想先跑通一个最小闭环，建议按这个顺序:

1. 阅读 [docs/00-overview.md](docs/00-overview.md)
2. 运行 [notebooks/00_overview/00_01_quickstart_end_to_end.ipynb](notebooks/00_overview/00_01_quickstart_end_to_end.ipynb)
3. 再看 [notebooks/00_overview/00_02_observing_rag_artifacts.ipynb](notebooks/00_overview/00_02_observing_rag_artifacts.ipynb)

这条路径的重点不是“调出最强效果”，而是先看清一次完整生命周期:

`initialize -> insert -> query -> inspect -> finalize`

### 3. 构建本地索引

仓库已经提供真实的索引维护脚本:

```bash
python scripts/build_index.py --action rebuild
```

只重建指定文档:

```bash
python scripts/build_index.py --action rebuild --doc-id <doc_id>
```

删除指定文档的索引产物:

```bash
python scripts/build_index.py --action delete --doc-id <doc_id>
```

### 4. 接入真实模型

很多 notebook 先用 deterministic stub 或 fallback backend 帮你建立心智模型。准备接入真实 provider 时，再配置 OpenAI-compatible 环境变量即可。项目已为 query、embedding、rerank、KG extraction 预留 provider 配置入口。

## 三条推荐学习路线

### 路线 A: 第一次系统学 RAG

按主线阅读:

1. [docs/00-overview.md](docs/00-overview.md)
2. [docs/01-rag-basics.md](docs/01-rag-basics.md)
3. [docs/02-data-loading-overview.md](docs/02-data-loading-overview.md)
4. [docs/03-indexing-overview.md](docs/03-indexing-overview.md)
5. [docs/04-retrieval-overview.md](docs/04-retrieval-overview.md)
6. [docs/05-generation-overview.md](docs/05-generation-overview.md)
7. [docs/06-evaluation-overview.md](docs/06-evaluation-overview.md)
8. [docs/07-optimization-overview.md](docs/07-optimization-overview.md)
9. [docs/08-system-architecture-overview.md](docs/08-system-architecture-overview.md)

### 路线 B: 以 notebook 为主做实验

建议先跑这些代表性 notebook:

- [00_01_quickstart_end_to_end.ipynb](notebooks/00_overview/00_01_quickstart_end_to_end.ipynb): 跑通最小闭环
- [03_07_build_index_pipeline.ipynb](notebooks/03_indexing/03_07_build_index_pipeline.ipynb): 看清索引构建到底写出了什么
- [04_04_hybrid_metadata_filter_and_modes.ipynb](notebooks/04_retrieval/04_04_hybrid_metadata_filter_and_modes.ipynb): 进入实用检索模式组合
- [04_05_fusion_rerank_and_topk.ipynb](notebooks/04_retrieval/04_05_fusion_rerank_and_topk.ipynb): 理解候选集合变化
- [06_05_eval_driven_debugging.ipynb](notebooks/06_evaluation/06_05_eval_driven_debugging.ipynb): 把评估信号变成调试动作

### 路线 C: 以代码为主理解系统实现

建议按这个顺序看代码:

1. [easyrag/rag/orchestrator.py](easyrag/rag/orchestrator.py)
2. [easyrag/rag/indexing/](easyrag/rag/indexing)
3. [easyrag/rag/retrieval/](easyrag/rag/retrieval)
4. [easyrag/rag/knowledge/](easyrag/rag/knowledge)
5. [easyrag/rag/storage/](easyrag/rag/storage)

配套文档入口:

- [docs/engineering/20-code-map.md](docs/engineering/20-code-map.md)
- [docs/engineering/21-indexing-pipeline.md](docs/engineering/21-indexing-pipeline.md)
- [docs/engineering/22-retrieval-pipeline.md](docs/engineering/22-retrieval-pipeline.md)
- [docs/engineering/23-generation-pipeline.md](docs/engineering/23-generation-pipeline.md)
- [docs/engineering/24-graph-curation-pipeline.md](docs/engineering/24-graph-curation-pipeline.md)
- [docs/engineering/25-local-vs-production-backends.md](docs/engineering/25-local-vs-production-backends.md)
- [docs/engineering/26-extension-guide.md](docs/engineering/26-extension-guide.md)

## 内容地图

| 模块 | 你会看到什么 | 最适合什么时候打开 |
| --- | --- | --- |
| [docs/README.md](docs/README.md) | 全部文档的总索引 | 想顺着课程主线学习时 |
| [notebooks/README.md](notebooks/README.md) | 全部 notebook 的阶段导航 | 想直接跑实验时 |
| [docs/principles/](docs/principles) | 方法论专题，如 chunking、hybrid retrieval、packing、evaluation | 想围绕单一主题做深入讲解时 |
| [docs/engineering/](docs/engineering) | 代码结构、运行链路与扩展点 | 想从教学内容落到实现时 |
| [scripts/build_index.py](scripts/build_index.py) | 索引构建与维护脚本 | 想把 demo 过渡到真实 repo-level workflow 时 |
| [sample_data/](sample_data) | 小型示例语料 | 想用极小数据集观察产物时 |
| [examples/README.md](examples/README.md) | 示例脚本目录 | 想了解未来脚本化入口的预留方向时 |

## 主线课程地图

| 阶段 | Docs | Notebook / 形态 | 关键词 |
| --- | --- | --- | --- |
| 00 Overview | [00-overview.md](docs/00-overview.md) | [00_01](notebooks/00_overview/00_01_quickstart_end_to_end.ipynb), [00_02](notebooks/00_overview/00_02_observing_rag_artifacts.ipynb) | 最小闭环、artifact 观察 |
| 01 RAG Basics | [01-rag-basics.md](docs/01-rag-basics.md) | docs-only | `Document`、`QueryResult`、阶段边界 |
| 02 Data Loading | [02-data-loading-overview.md](docs/02-data-loading-overview.md) | [02_01-02_05](notebooks/02_data_loading) | repo loading、manual docs、PDF、normalization |
| 03 Indexing | [03-indexing-overview.md](docs/03-indexing-overview.md) | [03_01-03_08](notebooks/03_indexing) | chunking、embeddings、vector index、workspace artifacts |
| 04 Retrieval | [04-retrieval-overview.md](docs/04-retrieval-overview.md) | [04_01-04_07](notebooks/04_retrieval) | preprocessing、rewrite、hybrid、fusion、rerank、hydration |
| 05 Generation | [05-generation-overview.md](docs/05-generation-overview.md) | [05_01-05_05](notebooks/05_generation) | evidence selection、packing、prompting、guardrails |
| 06 Evaluation | [06-evaluation-overview.md](docs/06-evaluation-overview.md) | [06_01-06_06](notebooks/06_evaluation) | tiny eval set、retrieval metrics、grounding、regression |
| 07 Optimization | [07-optimization-overview.md](docs/07-optimization-overview.md) | docs-only | 调优路线图、从评估回推优化 |
| 08 Architecture | [08-system-architecture-overview.md](docs/08-system-architecture-overview.md) | [08_01-08_03](notebooks/08_system_architecture) | code map、backend、observability、fallback |

## 核心教学对象

如果你只想先记住最重要的几个名字，先记这些:

- `EasyRAG`
- `QueryParam`
- `ChunkingConfig`
- `QueryResult`
- `KGExtractionConfig`

这些对象是连接文档、notebook 和代码实现的共同骨架。其中 `EasyRAG`、`QueryParam`、`QueryResult`、`KGExtractionConfig` 是直接面向使用者的重要接口，`ChunkingConfig` 则是理解索引阶段时非常关键的配置对象。

## 仓库结构

```text
EasyRAG/
├── easyrag/                # 核心库实现
│   ├── config/             # 环境、模型、存储配置
│   └── rag/
│       ├── indexing/       # loading / prepare / chunking / ingest
│       ├── retrieval/      # preprocess / query modes / fusion / hydration
│       ├── knowledge/      # entity / relation extraction and sync
│       └── storage/        # local and production-style storage backends
├── docs/                   # 主线文档、原理专题、工程专题
├── notebooks/              # 与 docs 同编号的教学实验
├── scripts/                # 仓库级索引维护脚本
├── sample_data/            # 小型示例语料
├── examples/               # 预留脚本示例
└── tests/                  # 聚焦核心行为的测试
```

## 开发与测试

运行当前核心测试集:

```bash
python -m pytest -q tests/test_config.py tests/test_rag_providers.py tests/test_rag_retriever.py tests/test_rag_graph_ops.py tests/test_rag_backends.py
```

如果你准备为这个仓库继续补内容，推荐优先遵循这条原则:

- 新的教学解释优先进入 `docs/`
- 新的实验优先进入 `notebooks/`
- 新的可复用能力再沉淀进 `easyrag/`

这样可以保持“教学叙事”和“工程接口”之间的边界清晰。

## 路线图

- 继续补齐 evaluation 与 optimization 的实验深度
- 把更多 retrieval / generation notebook 从 scaffold 补成可比较、可复现实验
- 增加更完整的 examples 脚本
- 补充更多 sample data、练习题和教学任务
- 继续完善 production concerns，如 observability、fallback、latency/cost tracking

## 相关索引

- [docs/README.md](docs/README.md)
- [notebooks/README.md](notebooks/README.md)
- [examples/README.md](examples/README.md)
- [sample_data/README.md](sample_data/README.md)

## 灵感来源

这个 README 的组织方式吸收了几个优秀教学仓库的优点:

- [pguso/rag-from-scratch](https://github.com/pguso/rag-from-scratch): 强调顺着 pipeline 学习与中间产物可观察
- [datawhalechina/hello-agents](https://github.com/datawhalechina/hello-agents): 强调“适合谁、能学到什么、如何开始”的低门槛导读
- [datawhalechina/all-in-rag](https://github.com/datawhalechina/all-in-rag): 强调内容地图、阶段拆分和系统化课程视角
