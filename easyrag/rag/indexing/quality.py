"""Quality checks for normalized ingestion documents."""

from __future__ import annotations

from collections import Counter
from typing import Any

from easyrag.support.optional_deps import Document
from easyrag.rag.indexing.normalization import normalize_document_text
from easyrag.rag.utils import tokenize

_SCANNED_PDF_PREFIX = "scanned pdf page"


def _collect_quality_flags(
    document: Document,
    *,
    doc_id_counts: Counter[str],
    content_counts: Counter[str],
) -> list[str]:
    metadata = dict(document.metadata)
    normalized_text = normalize_document_text(document.page_content)
    flags: list[str] = []
    if not normalized_text:
        flags.append("empty_after_normalization")
    if normalized_text and len(tokenize(normalized_text)) < 8:
        flags.append("very_short")
    doc_id = str(metadata.get("doc_id", "")).strip()
    if doc_id and doc_id_counts[doc_id] > 1:
        flags.append("duplicate_doc_id_in_batch")
    if normalized_text and content_counts[normalized_text] > 1:
        flags.append("duplicate_content_in_batch")
    if str(metadata.get("source_type", "")) == "pdf" and metadata.get("has_visual_content") and normalized_text.lower().startswith(_SCANNED_PDF_PREFIX):
        flags.append("pdf_visual_only")
    if not str(metadata.get("path", "")).strip():
        flags.append("missing_path")
    return flags


def annotate_document_quality(documents: list[Document]) -> tuple[list[Document], dict[str, Any]]:
    """Annotate documents with quality flags and skip empty normalized content."""

    doc_id_counts = Counter(str(document.metadata.get("doc_id", "")).strip() for document in documents if str(document.metadata.get("doc_id", "")).strip())
    content_counts = Counter(normalize_document_text(document.page_content) for document in documents if normalize_document_text(document.page_content))

    annotated: list[Document] = []
    quality_issue_counts: Counter[str] = Counter()
    skipped_documents = 0
    for document in documents:
        normalized_text = normalize_document_text(document.page_content)
        flags = _collect_quality_flags(document, doc_id_counts=doc_id_counts, content_counts=content_counts)
        quality_issue_counts.update(flags)
        metadata = dict(document.metadata)
        metadata["quality_flags"] = flags
        metadata["quality_issue_count"] = len(flags)
        annotated_document = Document(page_content=normalized_text, metadata=metadata)
        if "empty_after_normalization" in flags:
            skipped_documents += 1
            continue
        annotated.append(annotated_document)

    return annotated, {
        "quality_issue_counts": dict(sorted(quality_issue_counts.items())),
        "skipped_documents": skipped_documents,
    }
