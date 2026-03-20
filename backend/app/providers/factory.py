from app.core.config import Settings
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import LLMProvider


def get_provider(provider_name: str, settings: Settings) -> LLMProvider:
    provider = provider_name.lower()
    if provider == "anthropic":
        return AnthropicProvider(settings=settings)
    if provider in {"openai", "gemini", "mistral", "openai-compatible"}:
        raise NotImplementedError(f"Provider '{provider_name}' is stubbed and not implemented yet")
    raise ValueError(f"Unsupported provider '{provider_name}'")
