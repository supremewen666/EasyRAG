# Notebooks

The EasyRAG notebooks are organized by teaching stage and follow the same numbering and narrative order as the main `docs/` path.

## Stage directories

- `00_overview/`: main entry point, minimum viable loop, artifact inspection
- `02_data_loading/`: data loading, normalization, document quality
- `03_indexing/`: chunking, embeddings, vector index, build pipeline, workspace artifacts
- `04_retrieval/`: query normalization, rewriting, hybrid retrieval, fusion/rerank, hydration
- `05_generation/`: retrieval-to-answer handoff, evidence selection, packing, guardrails
- `06_evaluation/`: evaluation basics, tiny eval sets, retrieval metrics, grounding, regression
- `08_system_architecture/`: code map, backends, observability

## 00 Overview

- [00_01_quickstart_end_to_end.ipynb](00_overview/00_01_quickstart_end_to_end.ipynb): the minimum end-to-end loop
- [00_02_observing_rag_artifacts.ipynb](00_overview/00_02_observing_rag_artifacts.ipynb): inspecting intermediate objects and artifacts

## 02 Data loading

- [02_01_repo_loading_basics.ipynb](02_data_loading/02_01_repo_loading_basics.ipynb): repo loading, canonical `Document`, chunk preview
- [02_02_manual_document_preparation.ipynb](02_data_loading/02_02_manual_document_preparation.ipynb): manual documents and explicit metadata
- [02_03_pdf_and_multimodal_loading.ipynb](02_data_loading/02_03_pdf_and_multimodal_loading.ipynb): PDF and multimodal loading walkthrough
- [02_04_normalization_and_cleaning.ipynb](02_data_loading/02_04_normalization_and_cleaning.ipynb): normalization and cleaning
- [02_05_document_quality_and_edge_cases.ipynb](02_data_loading/02_05_document_quality_and_edge_cases.ipynb): document quality and edge cases

## 03 Indexing

- [03_01_chunking_principles.ipynb](03_indexing/03_01_chunking_principles.ipynb): chunking basics and strategy comparison
- [03_02_chunking_quality_analysis.ipynb](03_indexing/03_02_chunking_quality_analysis.ipynb): chunking comparison experiments
- [03_03_embeddings_basics.ipynb](03_indexing/03_03_embeddings_basics.ipynb): embedding basics and similarity intuition
- [03_04_normalization_before_embedding.ipynb](03_indexing/03_04_normalization_before_embedding.ipynb): normalization before embedding
- [03_05_embedding_inputs_and_provider_behavior.ipynb](03_indexing/03_05_embedding_inputs_and_provider_behavior.ipynb): provider behavior and input boundaries
- [03_06_vector_index_basics.ipynb](03_indexing/03_06_vector_index_basics.ipynb): vector index basics and backend behavior
- [03_07_build_index_pipeline.ipynb](03_indexing/03_07_build_index_pipeline.ipynb): workspace build, artifact inspection, query verification
- [03_08_storage_and_workspace_artifacts.ipynb](03_indexing/03_08_storage_and_workspace_artifacts.ipynb): workspace artifacts and storage inspection

## 04 Retrieval

- [04_01_query_normalization_and_preprocessing.ipynb](04_retrieval/04_01_query_normalization_and_preprocessing.ipynb): query normalization and preprocessing
- [04_02_query_rewrite_and_multi_query.ipynb](04_retrieval/04_02_query_rewrite_and_multi_query.ipynb): rewriting and multi-query retrieval
- [04_03_naive_retrieval_basics.ipynb](04_retrieval/04_03_naive_retrieval_basics.ipynb): naive retrieval baseline
- [04_04_hybrid_metadata_filter_and_modes.ipynb](04_retrieval/04_04_hybrid_metadata_filter_and_modes.ipynb): retrieval modes, hybrid retrieval, metadata filtering
- [04_05_fusion_rerank_and_topk.ipynb](04_retrieval/04_05_fusion_rerank_and_topk.ipynb): fusion, reranking, top-k
- [04_06_hydration_and_citations.ipynb](04_retrieval/04_06_hydration_and_citations.ipynb): hydration and citations
- [04_07_retrieval_failure_cases_and_debugging.ipynb](04_retrieval/04_07_retrieval_failure_cases_and_debugging.ipynb): retrieval failure cases and debugging

## 05 Generation

- [05_01_query_result_to_answer.ipynb](05_generation/05_01_query_result_to_answer.ipynb): retrieval-to-generation handoff
- [05_02_evidence_selection_and_topk_for_answering.ipynb](05_generation/05_02_evidence_selection_and_topk_for_answering.ipynb): evidence selection
- [05_03_context_assembly_and_packing.ipynb](05_generation/05_03_context_assembly_and_packing.ipynb): context packing
- [05_04_prompting_and_answer_style.ipynb](05_generation/05_04_prompting_and_answer_style.ipynb): prompting and answer style
- [05_05_generation_failures_and_guardrails.ipynb](05_generation/05_05_generation_failures_and_guardrails.ipynb): generation failure cases and guardrails

## 06 Evaluation

- [06_01_evaluation_basics.ipynb](06_evaluation/06_01_evaluation_basics.ipynb): what to evaluate and how to separate layers
- [06_02_building_a_tiny_eval_set.ipynb](06_evaluation/06_02_building_a_tiny_eval_set.ipynb): building a small teaching-oriented eval set
- [06_03_retrieval_metrics.ipynb](06_evaluation/06_03_retrieval_metrics.ipynb): retrieval metrics
- [06_04_answer_grounding_and_faithfulness.ipynb](06_evaluation/06_04_answer_grounding_and_faithfulness.ipynb): grounding and faithfulness
- [06_05_eval_driven_debugging.ipynb](06_evaluation/06_05_eval_driven_debugging.ipynb): evaluation-driven debugging
- [06_06_latency_cost_and_regression_checks.ipynb](06_evaluation/06_06_latency_cost_and_regression_checks.ipynb): latency, cost, and regression checks

## 08 System architecture

- [08_01_code_map_and_runtime_flow.ipynb](08_system_architecture/08_01_code_map_and_runtime_flow.ipynb): code map and runtime flow
- [08_02_local_vs_production_backends.ipynb](08_system_architecture/08_02_local_vs_production_backends.ipynb): local and production backends
- [08_03_observability_and_fallbacks.ipynb](08_system_architecture/08_03_observability_and_fallbacks.ipynb): observability, fallback, and operational concerns
