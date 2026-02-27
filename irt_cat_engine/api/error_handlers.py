"""Structured error handling utilities for API endpoints."""
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException

logger = logging.getLogger("irt_cat_engine.errors")


def generate_error_id() -> str:
    """Generate a unique error ID for tracking."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    return f"ERR-{timestamp}-{short_uuid}"


class AppError(HTTPException):
    """Base application error with structured response."""

    def __init__(
        self,
        status_code: int,
        error_type: str,
        message: str,
        user_message_ko: str | None = None,
        user_message_en: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.error_id = generate_error_id()
        self.error_type = error_type

        # Create structured detail
        detail = {
            "error_id": self.error_id,
            "error_type": error_type,
            "message": message,
            "user_message": {
                "ko": user_message_ko or message,
                "en": user_message_en or message,
            },
        }

        if details:
            detail["details"] = details

        super().__init__(status_code=status_code, detail=detail)

        # Log the error
        logger.error(
            f"[{self.error_id}] {error_type}: {message}",
            extra={"error_id": self.error_id, "details": details},
        )


class ValidationError(AppError):
    """Validation error (400)."""

    def __init__(
        self,
        message: str,
        user_message_ko: str | None = None,
        user_message_en: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=400,
            error_type="validation_error",
            message=message,
            user_message_ko=user_message_ko or "입력값이 올바르지 않습니다.",
            user_message_en=user_message_en or "Invalid input provided.",
            details=details,
        )


class NotFoundError(AppError):
    """Resource not found error (404)."""

    def __init__(
        self,
        resource: str,
        message: str | None = None,
        user_message_ko: str | None = None,
        user_message_en: str | None = None,
    ):
        super().__init__(
            status_code=404,
            error_type="not_found",
            message=message or f"{resource} not found",
            user_message_ko=user_message_ko or f"{resource}을(를) 찾을 수 없습니다.",
            user_message_en=user_message_en or f"{resource} not found.",
            details={"resource": resource},
        )


class ServerError(AppError):
    """Internal server error (500)."""

    def __init__(
        self,
        message: str,
        user_message_ko: str | None = None,
        user_message_en: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=500,
            error_type="server_error",
            message=message,
            user_message_ko=user_message_ko or "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            user_message_en=user_message_en or "Server error occurred. Please try again later.",
            details=details,
        )


class ServiceUnavailableError(AppError):
    """Service unavailable error (503)."""

    def __init__(
        self,
        service: str,
        message: str | None = None,
        user_message_ko: str | None = None,
        user_message_en: str | None = None,
    ):
        super().__init__(
            status_code=503,
            error_type="service_unavailable",
            message=message or f"{service} is not available",
            user_message_ko=user_message_ko or f"{service} 서비스를 사용할 수 없습니다.",
            user_message_en=user_message_en or f"{service} service is unavailable.",
            details={"service": service},
        )


def handle_unexpected_error(e: Exception, context: str = "") -> AppError:
    """Convert unexpected exceptions to structured errors."""
    error_id = generate_error_id()

    # Log the full exception
    logger.exception(
        f"[{error_id}] Unexpected error in {context}: {str(e)}",
        exc_info=True,
        extra={"error_id": error_id, "context": context},
    )

    # Return user-friendly error
    return ServerError(
        message=f"Unexpected error in {context}: {str(e)}",
        details={"context": context, "exception_type": type(e).__name__},
    )
