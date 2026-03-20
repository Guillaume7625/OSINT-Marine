from app.services.prompt_builder import PromptBuilder, PromptLayers


def test_prompt_builder_precedence_order():
    builder = PromptBuilder()
    prompt = builder.compose(
        PromptLayers(
            global_prompt="global",
            workspace_prompt="workspace",
            conversation_prompt="conversation",
            temporary_override="temp",
            summary_memory="summary",
            retrieved_context="retrieved",
        )
    )

    assert prompt == (
        "[GLOBAL_SYSTEM]\\nglobal\\n\\n"
        "[WORKSPACE]\\nworkspace\\n\\n"
        "[CONVERSATION]\\nconversation\\n\\n"
        "[TEMPORARY_OVERRIDE]\\ntemp\\n\\n"
        "[SUMMARY_MEMORY]\\nsummary\\n\\n"
        "[RETRIEVED_CONTEXT]\\nretrieved"
    )
