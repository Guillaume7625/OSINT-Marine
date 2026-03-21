from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.models import DocumentChunk, UploadedFile
from app.services.embeddings import EmbeddingModel, build_embedding_model
from app.storage.base import FileStorage


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
        uploaded_file = UploadedFile(
            conversation_id=conv_uuid,
            filename=filename,
            content_type=content_type,
            storage_path=str(stored_path),
            size_bytes=len(content),
            metadata_json={},
        )
        db.add(uploaded_file)
        db.flush()

        page_docs = self._extract_page_documents(path=stored_path, content_type=content_type)
        chunks = self._chunk_page_documents(page_docs)
        if not chunks:
            return uploaded_file, 0

        embeddings = self.embedding_model.embed([chunk["content"] for chunk in chunks])

        for item, emb in zip(chunks, embeddings, strict=True):
            db.add(
                DocumentChunk(
                    file_id=uploaded_file.id,
                    conversation_id=conv_uuid,
                    chunk_index=item["chunk_index"],
                    content=item["content"],
                    page_number=item.get("page_number"),
                    metadata_json={},
                    embedding=emb,
                )
            )

        db.flush()
        return uploaded_file, len(chunks)

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
            reader = PdfReader(str(path))
            pages: list[dict[str, Any]] = []
            for idx, page in enumerate(reader.pages, start=1):
                txt = page.extract_text() or ""
                if txt.strip():
                    pages.append({"page_number": idx, "text": txt})
            return pages

        text = path.read_text(encoding="utf-8", errors="ignore")
        return [{"page_number": None, "text": text}]

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
