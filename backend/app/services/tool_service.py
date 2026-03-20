from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.providers.base import ToolCall, ToolSpec
from app.services.rag_service import RagService
from app.tools.get_conversation_summary import get_conversation_summary_tool
from app.tools.list_uploaded_files import list_uploaded_files_tool
from app.tools.registry import all_tool_specs
from app.tools.search_documents import search_documents_tool


@dataclass(slots=True)
class ToolExecutionResult:
    call: ToolCall
    result: dict[str, Any]
    citations: list[dict[str, Any]] = field(default_factory=list)

    def as_message_content(self) -> str:
        return json.dumps(self.result, ensure_ascii=False)


class ToolService:
    def __init__(self, rag_service: RagService):
        self.rag_service = rag_service

    def specs(self) -> list[ToolSpec]:
        return all_tool_specs()

    async def execute_call(self, *, db: Session, conversation_id: str, call: ToolCall) -> ToolExecutionResult:
        name = call.name
        args = call.arguments or {}

        if name == "search_documents":
            query = str(args.get("query", "")).strip()
            top_k = int(args.get("top_k", 4))
            result = await search_documents_tool(
                rag_service=self.rag_service,
                db=db,
                conversation_id=conversation_id,
                query=query,
                top_k=top_k,
            )
            citations = [
                {
                    "filename": hit["filename"],
                    "chunk_index": hit["chunk_index"],
                    "page_number": hit.get("page_number"),
                }
                for hit in result.get("hits", [])
            ]
            return ToolExecutionResult(call=call, result=result, citations=citations)

        if name == "get_conversation_summary":
            result = get_conversation_summary_tool(db=db, conversation_id=conversation_id)
            return ToolExecutionResult(call=call, result=result)

        if name == "list_uploaded_files":
            result = list_uploaded_files_tool(db=db, conversation_id=conversation_id)
            return ToolExecutionResult(call=call, result=result)

        if name == "web_search":
            query = str(args.get("query", ""))
            return ToolExecutionResult(
                call=call,
                result={
                    "status": "stub",
                    "tool": "web_search",
                    "message": "web_search is intentionally stubbed in v1",
                    "query": query,
                },
            )

        if name == "python_exec":
            code = str(args.get("code", ""))
            return ToolExecutionResult(
                call=call,
                result={
                    "status": "stub",
                    "tool": "python_exec",
                    "message": "python_exec is intentionally stubbed in v1",
                    "code_preview": code[:160],
                },
            )

        return ToolExecutionResult(
            call=call,
            result={
                "status": "error",
                "message": f"Unknown tool {name}",
            },
        )
