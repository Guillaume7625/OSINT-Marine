from app.core.config import Settings
from app.domain.models import RoutingMode
from app.services.routing_policy import RoutingInput, RoutingPolicy


def _settings() -> Settings:
    return Settings(
        anthropic_model_fast="fast-model",
        anthropic_model_default="default-model",
        anthropic_model_complex="complex-model",
    )


def test_routing_policy_fast_for_simple_latency_sensitive():
    policy = RoutingPolicy(_settings())
    decision = policy.decide(
        RoutingInput(
            route_mode=RoutingMode.POLICY,
            task_type="chat",
            require_tools=False,
            require_rag=False,
            retrieved_context_chars=0,
            user_text="quick ping",
            latency_sensitive=True,
            user_preference_model=None,
            manual_model=None,
            locked_model=None,
        )
    )
    assert decision.model == "fast-model"


def test_routing_policy_defaults_to_quality_model_for_simple_chat():
    policy = RoutingPolicy(_settings())
    decision = policy.decide(
        RoutingInput(
            route_mode=RoutingMode.POLICY,
            task_type="chat",
            require_tools=False,
            require_rag=False,
            retrieved_context_chars=0,
            user_text="hello there",
            latency_sensitive=False,
            user_preference_model=None,
            manual_model=None,
            locked_model=None,
        )
    )
    assert decision.model == "default-model"


def test_routing_policy_complex_for_hard_context():
    policy = RoutingPolicy(_settings())
    decision = policy.decide(
        RoutingInput(
            route_mode=RoutingMode.POLICY,
            task_type="strategy",
            require_tools=True,
            require_rag=True,
            retrieved_context_chars=5000,
            user_text="word " * 260,
            latency_sensitive=False,
            user_preference_model=None,
            manual_model=None,
            locked_model=None,
        )
    )
    assert decision.model == "complex-model"


def test_routing_manual_mode_respects_manual_model():
    policy = RoutingPolicy(_settings())
    decision = policy.decide(
        RoutingInput(
            route_mode=RoutingMode.MANUAL,
            task_type="chat",
            require_tools=False,
            require_rag=False,
            retrieved_context_chars=0,
            user_text="hello",
            latency_sensitive=False,
            user_preference_model=None,
            manual_model="manual-choice",
            locked_model=None,
        )
    )
    assert decision.model == "manual-choice"
