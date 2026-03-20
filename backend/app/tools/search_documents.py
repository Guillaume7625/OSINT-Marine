from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.rag_service import RagService


async def search_documents_tool(
    *,
    rag_service: RagService,
    db: Session,
    conversation_id: str,
    query: str,
    top_k: int = 4,
) -> dict[str, Any]:
    retrieval = rag_service.retrieve(
        db=db,
        query=query,
        conversation_id=conversation_id,
        top_k=top_k,
    )

    return {
        "query": query,
        "hits": [
            {
                "chunk_id": str(hit["chunk_id"]),
                "filename": hit["filename"],
                "chunk_index": hit["chunk_index"],
                "page_number": hit.get("page_number"),
                "score": hit["score"],
                "content": hit["content"],
            }
            for hit in retrieval
        ],
    }
