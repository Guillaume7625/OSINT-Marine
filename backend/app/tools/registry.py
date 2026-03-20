from __future__ import annotations

from app.providers.base import ToolSpec


SEARCH_DOCUMENTS_TOOL = ToolSpec(
    name="search_documents",
    description="Search uploaded documents for relevant chunks and return citations.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "minimum": 1, "maximum": 10, "default": 4},
        },
        "required": ["query"],
    },
)

GET_CONVERSATION_SUMMARY_TOOL = ToolSpec(
    name="get_conversation_summary",
    description="Get the current summary memory for the conversation.",
    input_schema={
        "type": "object",
        "properties": {},
    },
)

LIST_UPLOADED_FILES_TOOL = ToolSpec(
    name="list_uploaded_files",
    description="List files uploaded for the current conversation.",
    input_schema={
        "type": "object",
        "properties": {},
    },
)

WEB_SEARCH_TOOL = ToolSpec(
    name="web_search",
    description="Stub: Search the web for up-to-date information.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
        },
        "required": ["query"],
    },
)

PYTHON_EXEC_TOOL = ToolSpec(
    name="python_exec",
    description="Stub: Execute Python code in a sandbox.",
    input_schema={
        "type": "object",
        "properties": {
            "code": {"type": "string"},
        },
        "required": ["code"],
    },
)


def all_tool_specs() -> list[ToolSpec]:
    return [
        SEARCH_DOCUMENTS_TOOL,
        GET_CONVERSATION_SUMMARY_TOOL,
        LIST_UPLOADED_FILES_TOOL,
        WEB_SEARCH_TOOL,
        PYTHON_EXEC_TOOL,
    ]
