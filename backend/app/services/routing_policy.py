from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.domain.models import RoutingMode


@dataclass(slots=True)
class RoutingInput:
    route_mode: RoutingMode
    task_type: str
    require_tools: bool
    require_rag: bool
    retrieved_context_chars: int
    user_text: str
    latency_sensitive: bool
    user_preference_model: str | None
    manual_model: str | None
    locked_model: str | None


@dataclass(slots=True)
class RoutingDecision:
    provider: str
    model: str
    routing_mode: RoutingMode
    tier: str
    rationale: str


class RoutingPolicy:
    def __init__(self, settings: Settings):
        self.settings = settings

    def decide(self, routing_input: RoutingInput) -> RoutingDecision:
        reasons: list[str] = []

        if routing_input.route_mode == RoutingMode.LOCKED and routing_input.locked_model:
            reasons.append("conversation is route-locked")
            return RoutingDecision(
                provider=self.settings.default_provider,
                model=routing_input.locked_model,
                routing_mode=RoutingMode.LOCKED,
                tier="locked",
                rationale="; ".join(reasons),
            )

        if routing_input.route_mode == RoutingMode.MANUAL:
            manual = routing_input.manual_model or routing_input.user_preference_model or self.settings.anthropic_model_default
            reasons.append("manual mode selected")
            return RoutingDecision(
                provider=self.settings.default_provider,
                model=manual,
                routing_mode=RoutingMode.MANUAL,
                tier="manual",
                rationale="; ".join(reasons),
            )

        complexity = self._complexity_score(routing_input.user_text)
        score = complexity
        reasons.append(f"base complexity score={complexity}")

        if routing_input.task_type in {"code", "strategy"}:
            score += 2
            reasons.append("task type indicates deeper reasoning")

        if routing_input.require_tools:
            score += 1
            reasons.append("tool use requested")

        if routing_input.require_rag:
            score += 1
            reasons.append("RAG retrieval requested")

        if routing_input.retrieved_context_chars > 4000:
            score += 1
            reasons.append("large retrieved context")

        if routing_input.latency_sensitive:
            score -= 2
            reasons.append("latency sensitive")

        if routing_input.user_preference_model:
            reasons.append("user preference provided")

        if score <= 0:
            tier = "fast"
            model = self.settings.anthropic_model_fast
        elif score >= 4:
            tier = "complex"
            model = self.settings.anthropic_model_complex
        else:
            tier = "default"
            model = self.settings.anthropic_model_default

        reasons.append(f"policy score={score} -> tier={tier}")

        return RoutingDecision(
            provider=self.settings.default_provider,
            model=model,
            routing_mode=RoutingMode.POLICY,
            tier=tier,
            rationale="; ".join(reasons),
        )

    def _complexity_score(self, text: str) -> int:
        token_count = len(text.split())
        if token_count < 20:
            return 0
        if token_count < 100:
            return 1
        if token_count < 250:
            return 2
        return 3
