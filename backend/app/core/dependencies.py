from functools import lru_cache

from app.core.config import get_settings
from app.services.chat_orchestrator import ChatOrchestrator
from app.services.context_manager import ContextManager
from app.services.prompt_builder import PromptBuilder
from app.services.rag_service import RagService
from app.services.routing_policy import RoutingPolicy
from app.services.tool_service import ToolService
from app.storage.local_storage import LocalFileStorage


@lru_cache
def get_storage() -> LocalFileStorage:
    settings = get_settings()
    return LocalFileStorage(root=settings.upload_root)


@lru_cache
def get_rag_service() -> RagService:
    return RagService(settings=get_settings(), storage=get_storage())


@lru_cache
def get_prompt_builder() -> PromptBuilder:
    return PromptBuilder()


@lru_cache
def get_routing_policy() -> RoutingPolicy:
    return RoutingPolicy(settings=get_settings())


@lru_cache
def get_context_manager() -> ContextManager:
    return ContextManager(settings=get_settings(), rag_service=get_rag_service())


@lru_cache
def get_tool_service() -> ToolService:
    return ToolService(rag_service=get_rag_service())


@lru_cache
def get_chat_orchestrator() -> ChatOrchestrator:
    return ChatOrchestrator(
        settings=get_settings(),
        prompt_builder=get_prompt_builder(),
        routing_policy=get_routing_policy(),
        context_manager=get_context_manager(),
        tool_service=get_tool_service(),
    )
