"""A test-only fake LLMProvider - lets us verify the extraction pipeline
(schema validation, error handling) without a live OpenAI/Ollama backend."""
from app.ai.base import LLMProvider
from app.core.exceptions import LLMUnavailableError


class MockLLMProvider(LLMProvider):
    provider_name = "mock"
    model_name = "mock-model"
    embedding_model_name = "mock-embed"

    def __init__(self, structured_response=None, raise_unavailable=False, raw_invalid_json=None):
        self._structured_response = structured_response
        self._raise_unavailable = raise_unavailable
        self._raw_invalid_json = raw_invalid_json

    async def generate(self, *, system_prompt, user_prompt, temperature=0.0, max_tokens=2000):
        return "mock text response"

    async def generate_structured(self, *, system_prompt, user_prompt, response_schema, temperature=0.0):
        if self._raise_unavailable:
            raise LLMUnavailableError("mock provider is down")
        if self._raw_invalid_json is not None:
            from app.ai.base import StructuredGenerationError
            raise StructuredGenerationError("mock invalid output")
        return self._structured_response

    async def embed(self, texts):
        return [[0.01 * i for i in range(8)] for _ in texts]

    async def health_check(self):
        return not self._raise_unavailable
