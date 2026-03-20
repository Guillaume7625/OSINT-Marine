from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PromptLayers:
    global_prompt: str
    workspace_prompt: str
    conversation_prompt: str | None = None
    temporary_override: str | None = None
    summary_memory: str | None = None
    retrieved_context: str | None = None


class PromptBuilder:
    """Compose prompt layers in deterministic order for easier testing and prompt caching."""

    ORDER = (
        ("GLOBAL_SYSTEM", "global_prompt"),
        ("WORKSPACE", "workspace_prompt"),
        ("CONVERSATION", "conversation_prompt"),
        ("TEMPORARY_OVERRIDE", "temporary_override"),
        ("SUMMARY_MEMORY", "summary_memory"),
        ("RETRIEVED_CONTEXT", "retrieved_context"),
    )

    def compose(self, layers: PromptLayers) -> str:
        sections: list[str] = []
        for title, attr in self.ORDER:
            value = getattr(layers, attr)
            if not value:
                continue
            cleaned = value.strip()
            if not cleaned:
                continue
            sections.append(f"[{title}]\\n{cleaned}")
        return "\\n\\n".join(sections)
