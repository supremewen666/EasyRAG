"""Canonical indexing pipeline modules."""

from easyrag.rag.indexing.chunking import ChunkingConfig, chunk_documents
from easyrag.rag.indexing.loaders import PdfReader, load_repo_documents
from easyrag.rag.indexing.maintenance import build_vector_index, rebuild_document_index
from easyrag.rag.indexing.pipeline import build_insert_payloads, ingest_documents
from easyrag.rag.indexing.prepare import prepare_documents_for_insert

__all__ = [
    "ChunkingConfig",
    "PdfReader",
    "build_vector_index",
    "build_insert_payloads",
    "chunk_documents",
    "ingest_documents",
    "load_repo_documents",
    "prepare_documents_for_insert",
    "rebuild_document_index",
]
