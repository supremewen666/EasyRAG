# Notebooks

EasyRAG 的 notebooks 现在按教学阶段组织，不再沿用旧的两层目录划分。

## 主线目录 / Stage Directories

- `00_overview/`: 总入口与最小闭环
- `02_data_loading/`: repo loading 与 manual documents
- `03_indexing/`: build index 与 chunking 对比
- `04_retrieval/`: query modes、KG、preprocess、fusion、rerank
- `05_generation/`: retrieval-to-answer handoff 与 generation labs
- `06_evaluation/`: eval basics、tiny eval set、retrieval metrics、grounding、eval-driven debugging
- `08_system_architecture/`: backend 与架构层补充

`07_optimization` 当前只在 docs 中占位，不创建 notebook 目录。

## 00 Overview

- [00_quickstart.ipynb](00_overview/00_quickstart.ipynb): 最小上手闭环

## 02 Data Loading

- [02_01_repo_loading.ipynb](02_data_loading/02_01_repo_loading.ipynb): repo loading、canonical `Document`、chunk preview
- [02_02_custom_documents.ipynb](02_data_loading/02_02_custom_documents.ipynb): manual documents 与显式 metadata

## 03 Indexing

- [03_01_build_index.ipynb](03_indexing/03_01_build_index.ipynb): workspace build、artifact inspection、query verification
- [03_02_chunking_strategy_lab.ipynb](03_indexing/03_02_chunking_strategy_lab.ipynb): chunking 对比实验

## 04 Retrieval

- [04_01_query_modes.ipynb](04_retrieval/04_01_query_modes.ipynb): 五种 retrieval mode 对比
- [04_02_knowledge_graph.ipynb](04_retrieval/04_02_knowledge_graph.ipynb): graph-aware retrieval
- [04_03_query_preprocessing_lab.ipynb](04_retrieval/04_03_query_preprocessing_lab.ipynb): query 预处理实验
- [04_04_vector_retrieval_lab.ipynb](04_retrieval/04_04_vector_retrieval_lab.ipynb): dense 与 fallback backend 对比
- [04_05_hybrid_fusion_lab.ipynb](04_retrieval/04_05_hybrid_fusion_lab.ipynb): hybrid/fusion 实验
- [04_06_rerank_lab.ipynb](04_retrieval/04_06_rerank_lab.ipynb): rerank 实验

## 05 Generation

- [05_01_generation_basics.ipynb](05_generation/05_01_generation_basics.ipynb): retrieval-to-generation handoff
- [05_02_top_k_selection_lab.ipynb](05_generation/05_02_top_k_selection_lab.ipynb): evidence selection
- [05_03_context_packing_lab.ipynb](05_generation/05_03_context_packing_lab.ipynb): context packing
- [05_04_prompting_and_answer_style_lab.ipynb](05_generation/05_04_prompting_and_answer_style_lab.ipynb): prompting 与 answer style
- [05_05_generation_failure_cases.ipynb](05_generation/05_05_generation_failure_cases.ipynb): generation failure cases

## 06 Evaluation

- [06_01_eval_basics.ipynb](06_evaluation/06_01_eval_basics.ipynb): 评估对象与分层
- [06_02_build_tiny_eval_set.ipynb](06_evaluation/06_02_build_tiny_eval_set.ipynb): 构造小型教学评测集
- [06_03_retrieval_metrics.ipynb](06_evaluation/06_03_retrieval_metrics.ipynb): retrieval metrics
- [06_04_grounding_and_faithfulness.ipynb](06_evaluation/06_04_grounding_and_faithfulness.ipynb): grounding 与 faithfulness
- [06_05_eval_driven_debugging.ipynb](06_evaluation/06_05_eval_driven_debugging.ipynb): 评估驱动调试

## 08 System Architecture

- [08_01_storage_backend_lab.ipynb](08_system_architecture/08_01_storage_backend_lab.ipynb): backend 视角的架构补充
