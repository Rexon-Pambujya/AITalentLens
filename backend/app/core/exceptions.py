"""
Application exception hierarchy + global FastAPI exception handlers.

Every error response returned by the API follows the same envelope
(section 39 of the spec):

    {
        "error_code": "INVALID_RESUME",
        "message": "Unsupported document format",
        "details": {...} | null,
        "request_id": "...",
        "timestamp": "..."
    }

Stack traces are NEVER exposed to the client, in any environment.
"""
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger, request_id_ctx

logger = get_logger(__name__)


class AppException(Exception):
    """Base class for all deliberate, expected application errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "APPLICATION_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"


class ValidationError(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "VALIDATION_ERROR"


class DuplicateResourceError(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "DUPLICATE_RESOURCE"


class AuthenticationError(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "AUTHORIZATION_ERROR"


class CrossTenantAccessError(AuthorizationError):
    """Raised whenever a request would leak data across organizations."""

    error_code = "CROSS_TENANT_ACCESS_DENIED"


class UnsupportedDocumentError(AppException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    error_code = "INVALID_RESUME"


class LLMUnavailableError(AppException):
    """Raised (and caught by services, not usually by clients) when the
    configured LLM provider cannot be reached. Services must degrade
    gracefully rather than letting this bubble to a 500 (section 62)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "AI_UNAVAILABLE"


def _envelope(error_code: str, message: str, details: Any = None) -> dict:
    return {
        "error_code": error_code,
        "message": message,
        "details": details,
        "request_id": request_id_ctx.get(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        logger.warning(
            "app_exception",
            error_code=exc.error_code,
            path=request.url.path,
            message=exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.error_code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope("REQUEST_VALIDATION_ERROR", "Invalid request payload", exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope("HTTP_ERROR", str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception):
        # Full detail goes to logs only; the client gets a generic message.
        logger.error("unhandled_exception", path=request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope("INTERNAL_SERVER_ERROR", "An unexpected error occurred."),
        )
