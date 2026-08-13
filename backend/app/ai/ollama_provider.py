"""
Ollama provider - fully local development path (section 3: "Ollama for
completely local development"), no API key or external network required.
"""
import json

import httpx
from pydantic import ValidationError

from app.ai.base import LLMProvider, StructuredGenerationError, T
from app.core.exceptions import LLMUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    provider_name = "ollama"

    def __init__(self, base_url: str, model: str, embedding_model: str):
        self.model_name = model
        self.embedding_model_name = embedding_model
        self._client = httpx.AsyncClient(base_url=base_url, timeout=60.0)

    async def generate(self, *, system_prompt, user_prompt, temperature=0.0, max_tokens=2000) -> str:
        try:
            response = await self._client.post(
                "/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except httpx.TransportError as exc:
            raise LLMUnavailableError(f"Could not reach Ollama at {self._client.base_url}: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMUnavailableError(f"Ollama returned {exc.response.status_code}") from exc

    async def generate_structured(self, *, system_prompt, user_prompt, response_schema: type[T], temperature=0.0) -> T:
        schema_hint = json.dumps(response_schema.model_json_schema(), indent=2)
        strict_system_prompt = (
            f"{system_prompt}\n\n"
            f"Respond with ONLY valid JSON matching this schema, no other text:\n{schema_hint}"
        )
        try:
            response = await self._client.post(
                "/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": strict_system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": temperature},
                },
            )
            response.raise_for_status()
        except httpx.TransportError as exc:
            raise LLMUnavailableError(f"Could not reach Ollama at {self._client.base_url}: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMUnavailableError(f"Ollama returned {exc.response.status_code}") from exc

        raw_content = response.json()["message"]["content"]
        try:
            return response_schema.model_validate_json(raw_content)
        except (ValidationError, json.JSONDecodeError) as exc:
            logger.warning("llm_structured_output_invalid", error=str(exc), raw=raw_content[:500])
            raise StructuredGenerationError(str(exc)) from exc

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        try:
            for text in texts:
                response = await self._client.post(
                    "/api/embeddings", json={"model": self.embedding_model_name, "prompt": text}
                )
                response.raise_for_status()
                vectors.append(response.json()["embedding"])
        except httpx.TransportError as exc:
            raise LLMUnavailableError(f"Could not reach Ollama at {self._client.base_url}: {exc}") from exc
        return vectors

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("/api/tags", timeout=3.0)
            return response.status_code == 200
        except httpx.TransportError:
            return False

    async def aclose(self) -> None:
        await self._client.aclose()
