# Data Loading Overview

This chapter covers the stage before indexing. In EasyRAG, data loading is where raw source material becomes canonical `Document` objects with stable IDs, paths, and metadata. If this stage is sloppy, the rest of the pipeline has to work around it.

## The learning question

How do repository files, manual texts, and document-specific loaders all converge on one `Document` abstraction that later indexing and retrieval can trust?

## The loading flow

At a high level, the loading stage looks like this:

```text
raw source material
  -> file discovery or explicit user input
  -> text extraction and normalization
  -> canonical metadata assignment
  -> Document objects
  -> chunk preview and quality checks
```

The output of this stage is not a workspace yet. It is a clean, inspectable set of documents that indexing can build on.

## The three main entry paths

### Repository loading

`EasyRAG.load_repo_documents()` is the default entry point for repository-shaped knowledge. It discovers indexable files, reads them, and attaches metadata such as:

- `title`
- `path`
- `relative_path`
- `doc_id`
- `source_type`

This path is usually the easiest to teach because the file system already supplies a lot of useful structure.

### Manual document preparation

`prepare_documents_for_insert()` and `EasyRAG.prepare_documents()` exist for cases where your corpus starts as strings instead of files. That is common in:

- evaluation notebooks
- scratch experiments
- application-generated notes
- one-off demos with explicit IDs and titles

The key point is that manual preparation is not a second-class path. It should produce the same stable `Document` shape as repository loading.

### PDF and document-specific extraction

Some sources need extraction before they can behave like normal text inputs. EasyRAG already treats PDFs as loadable source material. Conceptually, the rule stays the same:

- extract text into a consistent representation
- preserve enough location metadata to make later citations useful
- keep the canonical `Document` contract stable

This is why data loading deserves its own stage. Not every source starts as a clean Markdown file.

## Why metadata discipline matters

The system uses metadata for much more than bookkeeping. Titles, paths, IDs, and source types later affect:

- grounded citations
- workspace storage keys
- document status tracking
- debugging and evaluation

If metadata is unstable, citations drift and evaluations become harder to trust. Good loading is not just about getting text into memory. It is about making later artifacts easy to explain.

## Input quality shows up downstream

Loading is also the first place where you can catch problems that will otherwise surface much later:

- missing or noisy text extraction
- unstable paths or duplicated IDs
- source files that should not be indexed
- documents whose structure suggests poor chunk boundaries

That is why the loading notebooks stop to inspect canonical documents and chunk previews before any persistent workspace is built.

## Where this stage maps to code

The main loading-side responsibilities live here:

- `easyrag/rag/indexing/loaders.py`
- `easyrag/rag/indexing/prepare.py`
- `EasyRAG.load_repo_documents()`
- `EasyRAG.prepare_documents()`

The indexing pipeline depends on these entry points, but it should not need to care where the text originally came from once the `Document` objects are clean.

## Notebook handoff

The most direct companions to this chapter are:

- [02_01_repo_loading.ipynb](../notebooks/02_data_loading/02_01_repo_loading.ipynb), which shows repository discovery, canonical metadata, and chunk previews
- [02_02_custom_documents.ipynb](../notebooks/02_data_loading/02_02_custom_documents.ipynb), which shows the manual path with explicit IDs and logical paths

Together, those notebooks show the two main ways knowledge enters EasyRAG today.

## Where to go next

- Continue with [03-indexing-overview.md](03-indexing-overview.md) to see how loaded documents become summaries, vectors, graph state, and storage artifacts.
- Run [03_01_build_index.ipynb](../notebooks/03_indexing/03_01_build_index.ipynb) once you want to move from clean inputs to a persistent workspace.
