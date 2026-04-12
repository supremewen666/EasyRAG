# Data Loading Overview

This chapter covers the stage before indexing. In EasyRAG, data loading is where raw source material becomes canonical `Document` objects with stable text, IDs, paths, and metadata. If this stage is noisy, every later stage has to compensate for it.

## The learning question

How do repository files, manual texts, and extraction-heavy sources all converge on one `Document` contract that indexing and retrieval can trust?

## The loading flow

```text
raw source material
  -> file discovery or explicit user input
  -> extraction and normalization
  -> canonical metadata assignment
  -> Document objects
  -> document-quality checks
```

The output of this stage is not a workspace yet. It is a clean, inspectable collection of records that indexing can build on.

## What you will learn

- why loading is a real stage, not a trivial pre-step
- how repository loading and manual preparation meet at the same `Document` abstraction
- why normalization belongs in loading, not only in retrieval
- which document-level problems are worth catching before you ever build an index

## Key concepts

### Repository loading

`EasyRAG.load_repo_documents()` is the default path for repository-shaped knowledge. It discovers indexable files, reads them, and attaches metadata such as:

- `title`
- `path`
- `relative_path`
- `doc_id`
- `source_type`

This path is easy to teach because the file system already gives you structure, titles, and stable locations.

### Manual document preparation

`prepare_documents_for_insert()` and `EasyRAG.prepare_documents()` exist for corpora that start as strings, API outputs, notes, or synthetic evaluation items. The important point is that this path should not create a weaker object. It should still produce the same stable `Document` shape as repository loading.

### Extraction-heavy sources

Some sources need an extraction pass before they behave like normal text:

- PDFs
- mixed-layout documents
- multimodal or page-based inputs

The rule stays the same: extract into a consistent text representation, preserve enough location metadata for later citations, and keep the canonical `Document` contract stable.

## Normalization

Normalization is one of the cross-cutting ideas of the whole curriculum, and it starts here.

At the loading stage, normalization usually means:

- Unicode cleanup
- whitespace and newline normalization
- title and path cleanup
- punctuation normalization where extraction introduced noise
- repeated boilerplate removal
- duplicate or near-duplicate detection before indexing

This is not cosmetic cleanup. It changes what later chunking sees, what later embeddings encode, and how stable later citations feel.

## Industrial loading patterns

Small tutorials often stop at "read the file and move on." Real systems usually need a little more discipline:

- explicit include and exclude rules for source discovery
- metadata enrichment for source type, timestamps, and logical ownership
- template and boilerplate stripping
- deduplication before the workspace grows
- PII or sensitive-field handling
- document-quality checks before indexing starts

These are not advanced extras. They are often the cheapest place to improve the whole pipeline.

## Why metadata discipline matters

The system uses metadata for much more than bookkeeping. Titles, IDs, paths, and source types later affect:

- grounded citations
- workspace storage keys
- status tracking
- debugging
- evaluation

If metadata drifts, the downstream system still runs, but it becomes harder to explain.

## Notebook handoff

The direct notebook companions to this chapter are:

- [02_01_repo_loading_basics.ipynb](../notebooks/02_data_loading/02_01_repo_loading_basics.ipynb)
- [02_02_manual_document_preparation.ipynb](../notebooks/02_data_loading/02_02_manual_document_preparation.ipynb)
- [02_03_pdf_and_multimodal_loading.ipynb](../notebooks/02_data_loading/02_03_pdf_and_multimodal_loading.ipynb)
- [02_04_normalization_and_cleaning.ipynb](../notebooks/02_data_loading/02_04_normalization_and_cleaning.ipynb)
- [02_05_document_quality_and_edge_cases.ipynb](../notebooks/02_data_loading/02_05_document_quality_and_edge_cases.ipynb)

Some of these are deeper walkthroughs today, and some are still scaffolds. The directory order is still the intended learning order.

## Where to go next

- Continue with [03-indexing-overview.md](03-indexing-overview.md) to see how clean documents become derived retrieval artifacts.
- Run [03_07_build_index_pipeline.ipynb](../notebooks/03_indexing/03_07_build_index_pipeline.ipynb) once you want to move from stable inputs to a persistent workspace.
