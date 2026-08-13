from functools import lru_cache

from app.ai.base import LLMProvider
from app.core.config import get_settings

settings = get_settings()


def build_llm_provider() -> LLMProvider:
    """Constructs a brand-new, uncached provider instance. Use this (never
    the cached `get_llm_provider()`) from Celery tasks: each task runs in
    its own `asyncio.run(...)` event loop (see workers/resume_tasks.py and
    db/worker_session.py for the same constraint on the DB engine), and a
    provider's httpx.AsyncClient is bound to whichever loop it was first
    used on - reusing a cached one across tasks raises 'Event loop is
    closed' on the second+ task. Callers must `await provider.aclose()`
    when done."""
    if settings.LLM_PROVIDER == "openai":
        from app.ai.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            embedding_model=settings.OPENAI_EMBEDDING_MODEL,
        )

    if settings.LLM_PROVIDER == "groq":
        from app.ai.groq_provider import GroqProvider

        return GroqProvider(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            embedding_model=settings.GROQ_EMBEDDING_MODEL,
        )

    from app.ai.ollama_provider import OllamaProvider

    return OllamaProvider(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        embedding_model=settings.OLLAMA_EMBEDDING_MODEL,
    )


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Cached singleton for the FastAPI process (section 3: 'Allow provider
    selection through environment variables'). Safe to cache here because
    the API process runs one persistent event loop for its whole lifetime -
    unlike Celery tasks, see `build_llm_provider()`."""
    return build_llm_provider()
