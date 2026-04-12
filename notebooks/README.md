# Notebooks

EasyRAG 的 notebooks 现在按教学阶段组织，并与 `docs/` 主线保持同一编号和叙事顺序。

## 主线目录 / Stage Directories

- `00_overview/`: 总入口、最小闭环、artifact 观察
- `02_data_loading/`: data loading、normalization、document quality
- `03_indexing/`: chunking、embeddings、vector index、build pipeline、workspace artifacts
- `04_retrieval/`: query normalization、rewrite、hybrid retrieval、fusion/rerank、hydration
- `05_generation/`: retrieval-to-answer handoff、evidence selection、packing、guardrails
- `06_evaluation/`: eval basics、tiny eval set、retrieval metrics、grounding、regression
- `08_system_architecture/`: code map、backend、observability

说明：

- `01-rag-basics` 是 docs-only，不创建 notebook
- `07_optimization` 当前仍是 docs-only，不创建 notebook
- 目录与命名已经稳定，但不少 notebook 仍是 scaffold
- `Evaluation` 已经是完整主线，不再只是附录式补充

## 00 Overview

- [00_01_quickstart_end_to_end.ipynb](00_overview/00_01_quickstart_end_to_end.ipynb): 最小 end-to-end 闭环
- [00_02_observing_rag_artifacts.ipynb](00_overview/00_02_observing_rag_artifacts.ipynb): 中间对象与 artifact 观察

## 02 Data Loading

- [02_01_repo_loading_basics.ipynb](02_data_loading/02_01_repo_loading_basics.ipynb): repo loading、canonical `Document`、chunk preview
- [02_02_manual_document_preparation.ipynb](02_data_loading/02_02_manual_document_preparation.ipynb): manual documents 与显式 metadata
- [02_03_pdf_and_multimodal_loading.ipynb](02_data_loading/02_03_pdf_and_multimodal_loading.ipynb): PDF / multimodal 输入骨架
- [02_04_normalization_and_cleaning.ipynb](02_data_loading/02_04_normalization_and_cleaning.ipynb): normalization 与 cleaning
- [02_05_document_quality_and_edge_cases.ipynb](02_data_loading/02_05_document_quality_and_edge_cases.ipynb): 文档质量与边界情况

## 03 Indexing

- [03_01_chunking_principles.ipynb](03_indexing/03_01_chunking_principles.ipynb): chunking 基础骨架
- [03_02_chunking_quality_analysis.ipynb](03_indexing/03_02_chunking_quality_analysis.ipynb): chunking 对比实验
- [03_03_embeddings_basics.ipynb](03_indexing/03_03_embeddings_basics.ipynb): embeddings 基础骨架
- [03_04_normalization_before_embedding.ipynb](03_indexing/03_04_normalization_before_embedding.ipynb): embedding 前 normalization
- [03_05_embedding_inputs_and_provider_behavior.ipynb](03_indexing/03_05_embedding_inputs_and_provider_behavior.ipynb): provider 行为与输入边界
- [03_06_vector_index_basics.ipynb](03_indexing/03_06_vector_index_basics.ipynb): vector index 基础骨架
- [03_07_build_index_pipeline.ipynb](03_indexing/03_07_build_index_pipeline.ipynb): workspace build、artifact inspection、query verification
- [03_08_storage_and_workspace_artifacts.ipynb](03_indexing/03_08_storage_and_workspace_artifacts.ipynb): workspace artifacts 骨架

## 04 Retrieval

- [04_01_query_normalization_and_preprocessing.ipynb](04_retrieval/04_01_query_normalization_and_preprocessing.ipynb): query normalization 与 preprocessing
- [04_02_query_rewrite_and_multi_query.ipynb](04_retrieval/04_02_query_rewrite_and_multi_query.ipynb): rewrite 与 multi-query 骨架
- [04_03_naive_retrieval_basics.ipynb](04_retrieval/04_03_naive_retrieval_basics.ipynb): naive retrieval 骨架
- [04_04_hybrid_metadata_filter_and_modes.ipynb](04_retrieval/04_04_hybrid_metadata_filter_and_modes.ipynb): retrieval modes、hybrid、metadata filtering
- [04_05_fusion_rerank_and_topk.ipynb](04_retrieval/04_05_fusion_rerank_and_topk.ipynb): fusion、rerank、top-k
- [04_06_hydration_and_citations.ipynb](04_retrieval/04_06_hydration_and_citations.ipynb): hydration 与 citations
- [04_07_retrieval_failure_cases_and_debugging.ipynb](04_retrieval/04_07_retrieval_failure_cases_and_debugging.ipynb): retrieval failure cases 骨架

## 05 Generation

- [05_01_query_result_to_answer.ipynb](05_generation/05_01_query_result_to_answer.ipynb): retrieval-to-generation handoff
- [05_02_evidence_selection_and_topk_for_answering.ipynb](05_generation/05_02_evidence_selection_and_topk_for_answering.ipynb): evidence selection
- [05_03_context_assembly_and_packing.ipynb](05_generation/05_03_context_assembly_and_packing.ipynb): context packing
- [05_04_prompting_and_answer_style.ipynb](05_generation/05_04_prompting_and_answer_style.ipynb): prompting 与 answer style
- [05_05_generation_failures_and_guardrails.ipynb](05_generation/05_05_generation_failures_and_guardrails.ipynb): generation failure cases 与 guardrails

## 06 Evaluation

- [06_01_evaluation_basics.ipynb](06_evaluation/06_01_evaluation_basics.ipynb): 评估对象与分层
- [06_02_building_a_tiny_eval_set.ipynb](06_evaluation/06_02_building_a_tiny_eval_set.ipynb): 构造小型教学评测集
- [06_03_retrieval_metrics.ipynb](06_evaluation/06_03_retrieval_metrics.ipynb): retrieval metrics
- [06_04_answer_grounding_and_faithfulness.ipynb](06_evaluation/06_04_answer_grounding_and_faithfulness.ipynb): grounding 与 faithfulness
- [06_05_eval_driven_debugging.ipynb](06_evaluation/06_05_eval_driven_debugging.ipynb): 评估驱动调试
- [06_06_latency_cost_and_regression_checks.ipynb](06_evaluation/06_06_latency_cost_and_regression_checks.ipynb): latency、cost、regression checks

## 08 System Architecture

- [08_01_code_map_and_runtime_flow.ipynb](08_system_architecture/08_01_code_map_and_runtime_flow.ipynb): code map 与 runtime flow
- [08_02_local_vs_production_backends.ipynb](08_system_architecture/08_02_local_vs_production_backends.ipynb): local / production backend
- [08_03_observability_and_fallbacks.ipynb](08_system_architecture/08_03_observability_and_fallbacks.ipynb): observability、fallback、operational concerns
