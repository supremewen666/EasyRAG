"""Input normalization for document insertion."""

from __future__ import annotations

from typing import Sequence

from easyrag.support.optional_deps import Document
from easyrag.rag.indexing.normalization import normalize_document_text
from easyrag.rag.utils import slugify


def _prepare_documents(
    texts: str | Sequence[str],
    *,
    ids: Sequence[str] | None = None,
    file_paths: Sequence[str] | None = None,
) -> tuple[list[Document], dict[str, int]]:
    """Normalize raw insert inputs into Document objects and a small preparation report."""

    normalized_texts = [texts] if isinstance(texts, str) else list(texts)
    normalized_ids = list(ids) if ids is not None else []
    normalized_paths = list(file_paths) if file_paths is not None else []

    documents: list[Document] = []
    skipped_empty = 0
    for index, text in enumerate(normalized_texts):
        content = normalize_document_text(text)
        if not content:
            skipped_empty += 1
            continue
        path = (
            normalized_paths[index]
            if index < len(normalized_paths)
            else f"memory/doc_{index}.md"
        )
        title = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        doc_id = (
            normalized_ids[index]
            if index < len(normalized_ids) and normalized_ids[index].strip()
            else f"doc::{slugify(path)}"
        )
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source_type": "doc",
                    "path": path,
                    "relative_path": path,
                    "title": title,
                    "doc_id": doc_id,
                },
            )
        )
    return documents, {"empty_after_normalization": skipped_empty}


def prepare_documents_for_insert(
    texts: str | Sequence[str],
    *,
    ids: Sequence[str] | None = None,
    file_paths: Sequence[str] | None = None,
) -> list[Document]:
    """Normalize raw insert inputs into Document objects."""

    documents, _ = _prepare_documents(texts, ids=ids, file_paths=file_paths)
    return documents


def prepare_documents_for_insert_with_report(
    texts: str | Sequence[str],
    *,
    ids: Sequence[str] | None = None,
    file_paths: Sequence[str] | None = None,
) -> tuple[list[Document], dict[str, int]]:
    """Normalize raw insert inputs and return skipped-empty counts."""

    return _prepare_documents(texts, ids=ids, file_paths=file_paths)
