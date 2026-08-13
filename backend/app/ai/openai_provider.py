"""
OpenAI-compatible provider. Works against api.openai.com by default; also
works unmodified against any OpenAI-API-compatible endpoint (Azure OpenAI,
vLLM, LiteLLM proxy, etc.) by overriding the base URL, since we talk to it
over plain httpx rather than a heavier SDK.
"""
import json

import httpx
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.ai.base import LLMProvider, StructuredGenerationError, T
from app.core.exceptions import LLMUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

_OPENAI_BASE_URL = "https://api.openai.com/v1"


class OpenAIProvider(LLMProvider):
    provider_name = "openai"

    def __init__(self, api_key: str | None, model: str, embedding_model: str):
        self.model_name = model
        self.embedding_model_name = embedding_model
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=_OPENAI_BASE_URL,
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
            raise LLMUnavailableError("OPENAI_API_KEY is not configured")
        try:
            response = await self._client.post(path, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("openai_http_error", status=exc.response.status_code, body=exc.response.text[:500])
            raise LLMUnavailableError(f"OpenAI API returned {exc.response.status_code}") from exc
        except httpx.TransportError as exc:
            raise LLMUnavailableError(f"Could not reach OpenAI API: {exc}") from exc

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
            return response_schema.model_validate_json(raw_content)
        except (ValidationError, json.JSONDecodeError) as exc:
            logger.warning("llm_structured_output_invalid", error=str(exc), raw=raw_content[:500])
            raise StructuredGenerationError(str(exc)) from exc

    async def embed(self, texts: list[str]) -> list[list[float]]:
        data = await self._post("/embeddings", {"model": self.embedding_model_name, "input": texts})
        # OpenAI returns items possibly out of input order; sort by index defensively.
        ordered = sorted(data["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in ordered]

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
