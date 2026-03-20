from __future__ import annotations

import argparse
import json

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.domain.models import Conversation, DocumentChunk, RoutingMode
from app.services.rag_service import RagService
from app.storage.local_storage import LocalFileStorage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate nominal RAG path: upload -> chunk -> embed -> persist -> retrieve"
    )
    parser.add_argument("--text", required=True, help="Text content to ingest as an uploaded file")
    parser.add_argument("--query", required=True, help="Retrieval query to validate retrieval")
    parser.add_argument("--filename", default="rag_validation.txt", help="Virtual uploaded filename")
    parser.add_argument("--top-k", type=int, default=3, help="Number of retrieval hits")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()
    storage = LocalFileStorage(settings.upload_root)
    rag = RagService(settings=settings, storage=storage)

    with SessionLocal() as db:
        conversation = Conversation(
            title="RAG Validation",
            provider=settings.default_provider,
            routing_mode=RoutingMode.POLICY,
            metadata_json={"source": "validate_rag_nominal"},
        )
        db.add(conversation)
        db.flush()

        uploaded_file, chunks_created = rag.ingest_upload(
            db=db,
            filename=args.filename,
            content_type="text/plain",
            content=args.text.encode("utf-8"),
            conversation_id=str(conversation.id),
        )
        db.commit()

        persisted_chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.file_id == uploaded_file.id)
            .count()
        )

        hits = rag.retrieve(
            db=db,
            query=args.query,
            conversation_id=str(conversation.id),
            top_k=args.top_k,
        )

    payload = {
        "conversation_id": str(conversation.id),
        "file_id": str(uploaded_file.id),
        "chunks_created": chunks_created,
        "persisted_chunks": persisted_chunks,
        "retrieval_hit_count": len(hits),
        "top_hit": hits[0] if hits else None,
    }
    print(json.dumps(payload, indent=2, default=str))

    if chunks_created <= 0 or persisted_chunks <= 0 or len(hits) <= 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
