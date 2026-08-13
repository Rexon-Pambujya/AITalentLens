"""
LLM provider abstraction (section 3 / 61).

The rest of the codebase (extraction, matching, explanation) depends only
on this interface, never on `openai` or `httpx`-to-Ollama directly - so
swapping providers is an env var change, not a code change.

Every method must raise `LLMUnavailableError` (never a raw connection
error) on failure so callers can degrade gracefully (section 62).
"""
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    provider_name: str
    model_name: str
    embedding_model_name: str

    @abstractmethod
    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> str:
        """Free-form text generation. Prefer `generate_structured` wherever
        the output will be parsed programmatically - this exists mainly for
        prose (e.g. recruiter-facing explanations)."""

    @abstractmethod
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
        temperature: float = 0.0,
    ) -> T:
        """Generates output constrained to `response_schema` and returns a
        validated Pydantic instance. Implementations MUST validate the raw
        model output through `response_schema.model_validate_json` (or
        equivalent) before returning - callers never see unvalidated JSON
        (section 8: 'NEVER trust raw LLM output')."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Returns one embedding vector per input string, same order."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Cheap connectivity check - used by /health/ready and by services
        deciding whether to attempt AI calls at all this request."""

    async def aclose(self) -> None:
        """Releases any held connections (e.g. an httpx.AsyncClient). No-op
        by default; providers that hold a client override this. Celery
        tasks must call this on providers from `build_llm_provider()` since
        those are never cached/reused (see factory.py)."""


class StructuredGenerationError(Exception):
    """Raised internally when the LLM's output fails schema validation
    after retries are exhausted - callers catch this and fall back
    (section 62), they never see a raw JSONDecodeError."""
