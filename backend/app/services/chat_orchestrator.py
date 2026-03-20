from __future__ import annotations
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

import redis
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.models import Conversation, Message, MessageRole, PromptProfile, RoutingMode
from app.providers.base import ChatMessage, ChatRequest, UsageMetadata
from app.providers.factory import get_provider
from app.services.context_manager import ContextManager
from app.services.prompt_builder import PromptBuilder, PromptLayers
from app.services.routing_policy import RoutingDecision, RoutingInput, RoutingPolicy
from app.services.tool_service import ToolService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChatTurnOptions:
    route_mode: RoutingMode | None = None
    manual_model: str | None = None
    temporary_system_prompt: str | None = None
    task_type: str = "chat"
    latency_sensitive: bool = False
    require_tools: bool = True
    require_rag: bool = True
    user_model_preference: str | None = None


class ChatOrchestrator:
    def __init__(
        self,
        *,
        settings: Settings,
        prompt_builder: PromptBuilder,
        routing_policy: RoutingPolicy,
        context_manager: ContextManager,
        tool_service: ToolService,
    ):
        self.settings = settings
        self.prompt_builder = prompt_builder
        self.routing_policy = routing_policy
        self.context_manager = context_manager
        self.tool_service = tool_service
        try:
            self.redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        except Exception:  # noqa: BLE001
            self.redis = None

    async def stream_turn(
        self,
        *,
        db: Session,
        conversation: Conversation,
        user_text: str,
        options: ChatTurnOptions,
    ):
        started = time.perf_counter()
        stream_key = f"stream:{conversation.id}"

        self._persist_message(
            db=db,
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_text,
        )
        db.commit()

        if self.redis:
            self.redis.setex(stream_key, 300, "in_progress")

        context = self.context_manager.build(
            db=db,
            conversation_id=conversation.id,
            user_query=user_text,
            require_rag=options.require_rag,
        )

        route_mode = options.route_mode or conversation.routing_mode or RoutingMode(self.settings.default_routing_mode)
        if options.manual_model:
            conversation.manual_model = options.manual_model

        route_input = RoutingInput(
            route_mode=route_mode,
            task_type=options.task_type,
            require_tools=options.require_tools,
            require_rag=options.require_rag,
            retrieved_context_chars=len(context.retrieved_context or ""),
            user_text=user_text,
            latency_sensitive=options.latency_sensitive,
            user_preference_model=options.user_model_preference,
            manual_model=conversation.manual_model,
            locked_model=conversation.locked_model,
        )
        decision = self.routing_policy.decide(route_input)
        conversation.provider = decision.provider
        conversation.routing_mode = decision.routing_mode
        conversation.last_selected_model = decision.model

        profile = self._get_prompt_profile(db=db, conversation=conversation)
        layers = PromptLayers(
            global_prompt=profile.global_prompt,
            workspace_prompt=profile.workspace_prompt,
            conversation_prompt=conversation.conversation_prompt,
            temporary_override=options.temporary_system_prompt,
            summary_memory=context.summary_memory,
            retrieved_context=context.retrieved_context,
        )
        effective_prompt = self.prompt_builder.compose(layers)

        logger.info(
            "routing_decision conv_id=%s provider=%s model=%s mode=%s rationale=%s",
            conversation.id,
            decision.provider,
            decision.model,
            decision.routing_mode,
            decision.rationale,
        )
        logger.debug("effective_prompt conv_id=%s prompt=%s", conversation.id, effective_prompt)

        yield {
            "type": "meta",
            "provider": decision.provider,
            "model": decision.model,
            "routing_mode": decision.routing_mode.value,
            "routing_rationale": decision.rationale,
            "prompt_profile": profile.name,
            "effective_system_prompt": effective_prompt,
        }

        provider = get_provider(decision.provider, self.settings)
        citations = list(context.citations)
        working_messages = list(context.messages)

        if options.require_tools:
            await self._run_tool_loop(
                db=db,
                conversation=conversation,
                provider=provider,
                decision=decision,
                effective_prompt=effective_prompt,
                working_messages=working_messages,
                citations=citations,
            )

        stream_request = ChatRequest(
            messages=working_messages,
            model=decision.model,
            system_prompt=effective_prompt,
            max_tokens=self.settings.anthropic_max_tokens,
            tools=[],
        )

        full_text: list[str] = []
        usage = UsageMetadata()
        async for event in provider.stream(stream_request):
            if event.type == "text_delta":
                full_text.append(event.delta)
                if self.redis:
                    self.redis.setex(stream_key, 300, "streaming")
                yield {"type": "token", "delta": event.delta}
            elif event.type == "usage" and event.usage:
                usage = event.usage
            elif event.type == "error":
                yield {"type": "error", "error": event.error}
                raise RuntimeError(event.error)

        answer = "".join(full_text).strip()
        latency_ms = (time.perf_counter() - started) * 1000

        assistant_message = self._persist_message(
            db=db,
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=answer,
            provider=decision.provider,
            model=decision.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=latency_ms,
            citations=citations,
            metadata_json={
                "routing_mode": decision.routing_mode.value,
                "routing_rationale": decision.rationale,
                "prompt_profile": profile.name,
            },
        )

        conversation.total_input_tokens += usage.input_tokens
        conversation.total_output_tokens += usage.output_tokens
        conversation.total_latency_ms += latency_ms
        db.commit()

        if self.redis:
            self.redis.setex(stream_key, 120, "done")

        yield {
            "type": "done",
            "message_id": str(assistant_message.id),
            "citations": citations,
            "usage": {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
            },
            "latency_ms": round(latency_ms, 2),
        }

    async def _run_tool_loop(
        self,
        *,
        db: Session,
        conversation: Conversation,
        provider,
        decision: RoutingDecision,
        effective_prompt: str,
        working_messages: list[ChatMessage],
        citations: list[dict[str, Any]],
    ) -> None:
        for _ in range(self.settings.max_tool_iterations):
            request = ChatRequest(
                messages=working_messages,
                model=decision.model,
                system_prompt=effective_prompt,
                max_tokens=self.settings.anthropic_max_tokens,
                tools=self.tool_service.specs(),
            )
            response = await provider.complete(request)
            if not response.tool_calls:
                return

            assistant_tool_message = ChatMessage(
                role="assistant",
                content=response.message.content,
                tool_calls=response.tool_calls,
            )
            working_messages.append(assistant_tool_message)
            self._persist_message(
                db=db,
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=response.message.content,
                provider=decision.provider,
                model=decision.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                metadata_json={
                    "tool_calls": [
                        {"id": c.id, "name": c.name, "arguments": c.arguments}
                        for c in response.tool_calls
                    ]
                },
            )

            for call in response.tool_calls:
                tool_result = await self.tool_service.execute_call(
                    db=db,
                    conversation_id=str(conversation.id),
                    call=call,
                )
                citations.extend(tool_result.citations)
                content = tool_result.as_message_content()
                working_messages.append(
                    ChatMessage(
                        role="tool",
                        content=content,
                        tool_call_id=call.id,
                        tool_name=call.name,
                    )
                )
                self._persist_message(
                    db=db,
                    conversation_id=conversation.id,
                    role=MessageRole.TOOL,
                    content=content,
                    tool_name=call.name,
                    tool_call_id=call.id,
                    metadata_json={"tool_result": tool_result.result},
                )
            db.commit()

    def _get_prompt_profile(self, *, db: Session, conversation: Conversation) -> PromptProfile:
        if conversation.prompt_profile:
            return conversation.prompt_profile

        active = db.query(PromptProfile).filter(PromptProfile.is_active.is_(True)).first()
        if active:
            conversation.prompt_profile_id = active.id
            db.flush()
            return active

        bootstrap = PromptProfile(
            name="default",
            global_prompt=self.settings.bootstrap_global_prompt,
            workspace_prompt=self.settings.bootstrap_workspace_prompt,
            is_active=True,
        )
        db.add(bootstrap)
        db.flush()
        conversation.prompt_profile_id = bootstrap.id
        return bootstrap

    def _persist_message(
        self,
        *,
        db: Session,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        tool_name: str | None = None,
        tool_call_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        latency_ms: float | None = None,
        citations: list[dict] | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            citations=citations,
            metadata_json=metadata_json or {},
        )
        db.add(message)
        db.flush()
        return message
