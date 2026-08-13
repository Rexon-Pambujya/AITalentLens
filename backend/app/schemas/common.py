from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Any | None = None
    request_id: str
    timestamp: str


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]
