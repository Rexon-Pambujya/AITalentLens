"""
Groq provider - OpenAI-compatible API endpoint for fast inference.
https://groq.com/
"""
import json

import httpx
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.ai.base import LLMProvider, StructuredGenerationError, T
from app.core.exceptions import LLMUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def _strip_markdown_fence(text: str) -> str:
    """Defense-in-depth: response_format=json_object should prevent this,
    but strip a ```json ... ``` or ``` ... ``` wrapper if the model adds one
    anyway, rather than failing to parse valid JSON over a formatting quirk."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped[3:]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
    return stripped.strip()


class GroqProvider(LLMProvider):
    provider_name = "groq"

    def __init__(self, api_key: str | None, model: str, embedding_model: str):
        self.model_name = model
        self.embedding_model_name = embedding_model
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=_GROQ_BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
            timeout=30.0,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(httpx.TransportError),
        reraise=True,
    )
    async def _post(self, path: str, payload: dict) -> dict:
        if not self._api_key:
            raise LLMUnavailableError("GROQ_API_KEY is not configured")
        try:
            response = await self._client.post(path, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("groq_http_error", status=exc.response.status_code, body=exc.response.text[:500])
            raise LLMUnavailableError(f"Groq API returned {exc.response.status_code}") from exc
        except httpx.TransportError as exc:
            raise LLMUnavailableError(f"Could not reach Groq API: {exc}") from exc

    async def generate(self, *, system_prompt, user_prompt, temperature=0.0, max_tokens=2000) -> str:
        data = await self._post(
            "/chat/completions",
            {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        return data["choices"][0]["message"]["content"]

    async def generate_structured(self, *, system_prompt, user_prompt, response_schema: type[T], temperature=0.0) -> T:
        """Generate JSON matching the provided schema. Uses Groq's JSON-mode
        response_format (like OpenAIProvider) rather than relying on prompt
        instructions alone - the model sometimes wraps prompt-only JSON in a
        markdown code fence despite being told not to, which response_format
        prevents at the API level."""
        schema_hint = json.dumps(response_schema.model_json_schema(), indent=2)
        strict_system_prompt = (
            f"{system_prompt}\n\n"
            "Respond with ONLY a single valid JSON object matching this JSON Schema, "
            f"with no markdown fences, no commentary, no extra keys:\n{schema_hint}"
        )
        data = await self._post(
            "/chat/completions",
            {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": strict_system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "response_format": {"type": "json_object"},
            },
        )
        raw_content = data["choices"][0]["message"]["content"]
        try:
            return response_schema.model_validate_json(_strip_markdown_fence(raw_content))
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("groq_structured_output_error", raw_output=raw_content[:500], error=str(exc))
            raise StructuredGenerationError(f"Failed to parse Groq response as {response_schema.__name__}") from exc

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Groq does not provide embedding models.
        Use LLM_PROVIDER=openai with OPENAI_EMBEDDING_MODEL, or point
        OLLAMA_EMBEDDING_MODEL at a local model, to get embeddings while
        still using Groq for chat/extraction.
        """
        raise LLMUnavailableError(
            "Groq does not provide embedding models. "
            "Use LLM_PROVIDER=openai with OPENAI_EMBEDDING_MODEL, "
            "or add a separate embedding service."
        )

    async def health_check(self) -> bool:
        if not self._api_key:
            return False
        try:
            response = await self._client.get("/models", timeout=5.0)
            return response.status_code == 200
        except httpx.TransportError:
            return False

    async def aclose(self) -> None:
        await self._client.aclose()
