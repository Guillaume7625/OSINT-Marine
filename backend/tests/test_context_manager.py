from types import SimpleNamespace
import uuid

from app.core.config import Settings
from app.services.context_manager import ContextManager


def test_context_manager_refreshes_existing_summary(monkeypatch):
    settings = Settings(default_context_window_messages=2)
    context_manager = ContextManager(settings=settings, rag_service=SimpleNamespace(retrieve=lambda **kwargs: []))

    recent_messages = [
        SimpleNamespace(role=SimpleNamespace(value="user"), content="hello", tool_call_id=None, tool_name=None),
        SimpleNamespace(role=SimpleNamespace(value="assistant"), content="world", tool_call_id=None, tool_name=None),
    ]
    summary_calls: list[dict] = []

    monkeypatch.setattr(context_manager, "_get_existing_summary", lambda **kwargs: "old summary")
    monkeypatch.setattr(context_manager, "_load_recent_messages", lambda **kwargs: recent_messages)
    monkeypatch.setattr(
        context_manager,
        "_build_summary_from_recent_history",
        lambda **kwargs: summary_calls.append(kwargs) or "refreshed summary",
    )

    bundle = context_manager.build(
        db=SimpleNamespace(),
        conversation_id=uuid.uuid4(),
        user_query="What changed?",
        require_rag=False,
    )

    assert bundle.summary_memory == "refreshed summary"
    assert len(summary_calls) == 1
