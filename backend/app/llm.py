# SAFE FALLBACK LLM (NO MODEL REQUIRED)

def llm_generate(prompt: str, **kwargs) -> str:
    """
    Temporary fallback so the RAG pipeline works without a GGUF model.
    This intentionally does NOT load any LLM.
    """
    return (
        "LLM generation is disabled. "
        "Here are the most relevant email snippets retrieved for your query."
    )
