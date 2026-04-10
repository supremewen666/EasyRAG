"""Repository document loading and metadata helpers."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Sequence

from easyrag.support.optional_deps import Document
from easyrag.rag.utils import slugify

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional dependency path.
    PdfReader = None

_TEXT_SUFFIXES = {".md", ".mdx", ".rst", ".txt"}
_PDF_SUFFIXES = {".pdf"}
_EXCLUDED_PARTS = {".git", ".venv", "__pycache__", "node_modules", ".easyrag"}
_PREFERRED_DOC_DIRS = {"docs", "doc", "design", "adr", "adrs", "notes"}


def is_indexable_document(path: Path, repo_root: Path) -> bool:
    """Return whether a repository file should be loaded into RAG."""

    if any(part in _EXCLUDED_PARTS for part in path.parts):
        return False

    lower_name = path.name.lower()
    if lower_name.startswith("readme"):
        return True

    relative_parts = {part.lower() for part in path.relative_to(repo_root).parts}
    if path.suffix.lower() in _PDF_SUFFIXES:
        return bool(relative_parts & _PREFERRED_DOC_DIRS)
    if path.suffix.lower() not in _TEXT_SUFFIXES:
        return False
    return bool(relative_parts & _PREFERRED_DOC_DIRS) or lower_name in {
        "contributing.md",
        "architecture.md",
        "design.md",
        "roadmap.md",
        "setup.md",
        "install.md",
        "getting_started.md",
    }


def _save_pdf_page_images(page: object, path: Path, root: Path, *, page_number: int) -> list[str]:
    """Persist embedded PDF page images for later multimodal retrieval."""

    raw_images = getattr(page, "images", None)
    if not raw_images:
        return []
    try:
        images = list(raw_images)
    except TypeError:
        return []

    output_dir = root / ".easyrag" / "media" / path.stem / f"page-{page_number}"
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[str] = []
    for index, image in enumerate(images, start=1):
        image_name = Path(str(getattr(image, "name", f"image-{index}.png"))).name or f"image-{index}.png"
        suffix = Path(image_name).suffix or ".png"
        output_path = output_dir / f"image-{index}{suffix}"

        data = getattr(image, "data", None)
        if isinstance(data, bytes) and data:
            output_path.write_bytes(data)
            saved_paths.append(str(output_path))
            continue

        pil_image = getattr(image, "image", None)
        if pil_image is None:
            continue
        buffer = io.BytesIO()
        try:
            pil_image.save(buffer, format=(pil_image.format or "PNG"))
        except Exception:
            continue
        output_path = output_path.with_suffix(f".{(pil_image.format or 'png').lower()}")
        output_path.write_bytes(buffer.getvalue())
        saved_paths.append(str(output_path))
    return saved_paths


def build_document_metadata(
    path: Path,
    root: Path,
    *,
    source_type: str,
    page_number: int | None = None,
    image_paths: Sequence[str] | None = None,
) -> dict[str, object]:
    """Build canonical metadata for a loaded repository document."""

    relative_path = str(path.relative_to(root))
    title = path.stem
    doc_id = f"doc::{slugify(relative_path)}"
    if page_number is not None:
        doc_id = f"{doc_id}::page::{page_number}"
    metadata: dict[str, object] = {
        "source_type": source_type,
        "path": str(path),
        "relative_path": relative_path,
        "title": title,
        "doc_id": doc_id,
    }
    if page_number is not None:
        metadata["page_number"] = page_number
    if image_paths:
        metadata["image_paths"] = list(image_paths)
        metadata["has_visual_content"] = True
    return metadata


def load_pdf_documents(path: Path, root: Path) -> list[Document]:
    """Load text pages from a PDF file."""

    if PdfReader is None:
        return []
    try:
        reader = PdfReader(str(path))
    except Exception:
        return []

    documents: list[Document] = []
    for page_number, page in enumerate(reader.pages, start=1):
        image_paths = _save_pdf_page_images(page, path, root, page_number=page_number)
        try:
            text = (page.extract_text() or "").strip()
        except Exception:
            text = ""
        if not text and not image_paths:
            continue
        if not text and image_paths:
            text = f"Scanned PDF page {page_number} from {path.stem}."
        documents.append(
            Document(
                page_content=text,
                metadata=build_document_metadata(path, root, source_type="pdf", page_number=page_number, image_paths=image_paths),
            )
        )
    return documents


def load_repo_documents(repo_root: str | Path) -> list[Document]:
    """Load repository documents suitable for knowledge indexing."""

    root = Path(repo_root).resolve()
    documents: list[Document] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not is_indexable_document(path, root):
            continue
        if path.suffix.lower() in _PDF_SUFFIXES:
            documents.extend(load_pdf_documents(path, root))
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            continue
        documents.append(
            Document(
                page_content=text,
                metadata=build_document_metadata(path, root, source_type="doc"),
            )
        )
    return documents


__all__ = [
    "PdfReader",
    "build_document_metadata",
    "is_indexable_document",
    "load_pdf_documents",
    "load_repo_documents",
]
