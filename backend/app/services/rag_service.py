from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.models import DocumentChunk, UploadedFile
from app.services.embeddings import EmbeddingModel, build_embedding_model
from app.storage.base import FileStorage
from app.core.database import SessionLocal

IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


class RagService:
    def __init__(self, settings: Settings, storage: FileStorage, embedding_model: EmbeddingModel | None = None):
        self.settings = settings
        self.storage = storage
        self.embedding_model = embedding_model or build_embedding_model(settings)

    def ingest_upload(
        self,
        *,
        db: Session,
        filename: str,
        content_type: str,
        content: bytes,
        conversation_id: str | None,
    ) -> tuple[UploadedFile, int]:
        stored_path = self.storage.save_bytes(filename=filename, content=content)

        conv_uuid = uuid.UUID(conversation_id) if conversation_id else None
        uploaded_file = self.register_upload(
            db=db,
            filename=filename,
            content_type=content_type,
            storage_path=stored_path,
            size_bytes=len(content),
            conversation_id=conv_uuid,
            status="processing",
        )
        chunks = self._process_uploaded_file(db=db, uploaded_file=uploaded_file)
        self._update_upload_metadata(
            db=db,
            uploaded_file=uploaded_file,
            status="done",
            chunks_created=chunks,
        )
        db.flush()
        return uploaded_file, chunks

    def register_upload(
        self,
        *,
        db: Session,
        filename: str,
        content_type: str,
        storage_path: Path,
        size_bytes: int,
        conversation_id: uuid.UUID | None,
        status: str = "queued",
    ) -> UploadedFile:
        uploaded_file = UploadedFile(
            conversation_id=conversation_id,
            filename=filename,
            content_type=content_type,
            storage_path=str(storage_path),
            size_bytes=size_bytes,
            metadata_json={
                "ingestion_status": status,
                "chunks_created": 0,
                "ingestion_error": None,
            },
        )
        db.add(uploaded_file)
        db.flush()
        return uploaded_file

    def process_uploaded_file(self, uploaded_file_id: str) -> str:
        try:
            file_uuid = uuid.UUID(uploaded_file_id)
        except ValueError:
            return "error"

        with SessionLocal() as db:
            uploaded_file = db.get(UploadedFile, file_uuid)
            if not uploaded_file:
                return "missing"
            if uploaded_file.ingestion_status == "done":
                return "done"

            self._update_upload_metadata(db=db, uploaded_file=uploaded_file, status="processing")
            db.commit()

            try:
                chunks_created = self._process_uploaded_file(db=db, uploaded_file=uploaded_file)
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                uploaded_file = db.get(UploadedFile, file_uuid)
                if not uploaded_file:
                    return "error"
                self._update_upload_metadata(
                    db=db,
                    uploaded_file=uploaded_file,
                    status="error",
                    chunks_created=0,
                    ingestion_error=str(exc),
                )
                db.commit()
                return "error"

            self._update_upload_metadata(
                db=db,
                uploaded_file=uploaded_file,
                status="done",
                chunks_created=chunks_created,
            )
            db.commit()
            return "done"

    def _process_uploaded_file(self, *, db: Session, uploaded_file: UploadedFile) -> int:
        path = Path(uploaded_file.storage_path)
        page_docs = self._extract_page_documents(path=path, content_type=uploaded_file.content_type)
        chunks = self._chunk_page_documents(page_docs)
        if not chunks:
            return 0

        embeddings = self.embedding_model.embed([chunk["content"] for chunk in chunks])

        for item, emb in zip(chunks, embeddings, strict=True):
            db.add(
                DocumentChunk(
                    file_id=uploaded_file.id,
                    conversation_id=uploaded_file.conversation_id,
                    chunk_index=item["chunk_index"],
                    content=item["content"],
                    page_number=item.get("page_number"),
                    metadata_json={},
                    embedding=emb,
                )
            )

        db.flush()
        return len(chunks)

    def _update_upload_metadata(
        self,
        *,
        db: Session,
        uploaded_file: UploadedFile,
        status: str,
        chunks_created: int | None = None,
        ingestion_error: str | None = None,
    ) -> None:
        metadata = dict(uploaded_file.metadata_json or {})
        metadata["ingestion_status"] = status
        if chunks_created is not None:
            metadata["chunks_created"] = chunks_created
        if ingestion_error is not None:
            metadata["ingestion_error"] = ingestion_error
        elif status != "error":
            metadata["ingestion_error"] = None
        uploaded_file.metadata_json = metadata
        db.add(uploaded_file)

    def retrieve(
        self,
        *,
        db: Session,
        query: str,
        conversation_id: str | None,
        top_k: int,
    ) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        if top_k <= 0:
            return []

        if conversation_id:
            try:
                conv_uuid = uuid.UUID(conversation_id)
            except ValueError:
                conv_uuid = None

            if conv_uuid:
                has_chunks = db.query(DocumentChunk.id).filter(DocumentChunk.conversation_id == conv_uuid).first()
                if not has_chunks:
                    return []
            else:
                conv_uuid = None
        else:
            conv_uuid = None

        query_embedding = self.embedding_model.embed([query])[0]
        distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")

        qry = db.query(
            DocumentChunk,
            UploadedFile,
            distance_expr,
        ).join(UploadedFile, UploadedFile.id == DocumentChunk.file_id)

        if conv_uuid:
            qry = qry.filter(DocumentChunk.conversation_id == conv_uuid)

        rows = qry.order_by("distance").limit(top_k).all()

        results: list[dict[str, Any]] = []
        for chunk, file_obj, distance in rows:
            score = float(max(0.0, 1.0 - float(distance)))
            results.append(
                {
                    "chunk_id": chunk.id,
                    "filename": file_obj.filename,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "score": round(score, 4),
                    "content": chunk.content,
                }
            )
        return results

    def _extract_page_documents(self, *, path: Path, content_type: str) -> list[dict[str, Any]]:
        suffix = path.suffix.lower()
        if content_type == "application/pdf" or suffix == ".pdf":
            return self._extract_pdf_documents(path)

        if suffix in IMAGE_SUFFIXES or content_type.startswith("image/"):
            text = self._ocr_image_file(path)
            return [{"page_number": 1, "text": text}] if text.strip() else []

        text = path.read_text(encoding="utf-8", errors="ignore")
        return [{"page_number": None, "text": text}]

    def _extract_pdf_documents(self, path: Path) -> list[dict[str, Any]]:
        reader = PdfReader(str(path))
        pages: list[dict[str, Any]] = []
        ocr_pages: list[int] = []

        for idx, page in enumerate(reader.pages, start=1):
            txt = page.extract_text() or ""
            if txt.strip():
                pages.append({"page_number": idx, "text": txt})
            else:
                ocr_pages.append(idx)

        if ocr_pages:
            pages.extend(self._ocr_pdf_pages(path=path, page_numbers=ocr_pages))

        return pages

    def _ocr_pdf_pages(self, *, path: Path, page_numbers: list[int]) -> list[dict[str, Any]]:
        if not page_numbers:
            return []

        rendered_pages: list[dict[str, Any]] = []
        max_workers = min(4, len(page_numbers))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._ocr_pdf_page, path=path, page_number=page_number): page_number
                for page_number in page_numbers
            }
            for future in as_completed(futures):
                page_number = futures[future]
                text = future.result().strip()
                if text:
                    rendered_pages.append({"page_number": page_number, "text": text})

        rendered_pages.sort(key=lambda item: item["page_number"] or 0)
        return rendered_pages

    def _ocr_pdf_page(self, *, path: Path, page_number: int) -> str:
        try:
            from pdf2image import convert_from_path
        except ModuleNotFoundError:
            return ""

        try:
            images = convert_from_path(
                str(path),
                first_page=page_number,
                last_page=page_number,
                dpi=200,
            )
        except Exception:  # noqa: BLE001
            return ""

        if not images:
            return ""

        return self._ocr_pil_image(images[0])

    def _ocr_image_file(self, path: Path) -> str:
        try:
            from PIL import Image
        except ModuleNotFoundError:
            return ""

        try:
            with Image.open(path) as image:
                return self._ocr_pil_image(image)
        except Exception:  # noqa: BLE001
            return ""

    def _ocr_pil_image(self, image: Any) -> str:
        try:
            import pytesseract
        except ModuleNotFoundError:
            return ""

        try:
            return pytesseract.image_to_string(image).strip()
        except Exception:  # noqa: BLE001
            return ""

    def _chunk_page_documents(self, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        chunk_size = self.settings.rag_chunk_size
        overlap = self.settings.rag_chunk_overlap
        output: list[dict[str, Any]] = []
        idx = 0

        for page in pages:
            text = page["text"]
            start = 0
            while start < len(text):
                end = min(len(text), start + chunk_size)
                snippet = text[start:end].strip()
                if snippet:
                    output.append(
                        {
                            "chunk_index": idx,
                            "content": snippet,
                            "page_number": page.get("page_number"),
                        }
                    )
                    idx += 1
                if end >= len(text):
                    break
                start = max(0, end - overlap)

        return output
