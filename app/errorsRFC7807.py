from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Кастомное исключение приложения с кодом ошибки"""

    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


def create_problem_response(
    status: int,
    title: str,
    detail: str,
    error_type: str = "about:blank",
    error_code: str = None,
    instance: str = None,
    extras: Dict[str, Any] = None,
) -> JSONResponse:
    """
    Создает RFC 7807 compliant ответ об ошибке

    Args:
        status: HTTP статус код
        title: Краткое описание ошибки
        detail: Детальное описание ошибки
        error_type: URI идентификатор типа ошибки
        error_code: Внутренний код ошибки для обратной совместимости
        instance: URI конкретного экземпляра ошибки
        extras: Дополнительные поля
    """
    correlation_id = str(uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"

    payload = {
        "type": error_type,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance,
        "correlation_id": correlation_id,
        "timestamp": timestamp,
    }

    # Добавляем code для обратной совместимости
    if error_code:
        payload["code"] = error_code

    # Добавляем дополнительные поля
    if extras:
        payload.update(extras)

    return JSONResponse(
        status_code=status,
        content=payload,
        headers={"Content-Type": "application/problem+json"},
    )


async def api_error_handler(request: Request, exc: ApiError):
    """Обработчик кастомных ошибок приложения"""
    error_type = f"https://habittracker.com/errors/{exc.code.lower().replace('_', '-')}"

    return create_problem_response(
        status=exc.status,
        title=exc.code.replace("_", " ").title(),
        detail=exc.message,
        error_type=error_type,
        error_code=exc.code,
        instance=request.url.path,
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик стандартных HTTP исключений"""
    detail = exc.detail if isinstance(exc.detail, str) else "An error occurred"

    # Маппинг стандартных HTTP ошибок
    error_mapping = {
        400: ("Bad Request", "validation-error"),
        401: ("Unauthorized", "authentication-error"),
        403: ("Forbidden", "authorization-error"),
        404: ("Not Found", "not-found"),
        405: ("Method Not Allowed", "method-not-allowed"),
        409: ("Conflict", "conflict"),
        422: ("Unprocessable Entity", "validation-error"),
        429: ("Too Many Requests", "rate-limit-exceeded"),
        500: ("Internal Server Error", "internal-error"),
        503: ("Service Unavailable", "service-unavailable"),
    }

    title, error_code = error_mapping.get(
        exc.status_code, ("Internal Server Error", "internal-error")
    )

    error_type = f"https://habittracker.com/errors/{error_code}"

    return create_problem_response(
        status=exc.status_code,
        title=title,
        detail=detail,
        error_type=error_type,
        error_code=error_code.upper().replace("-", "_"),
        instance=request.url.path,
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик непредвиденных исключений"""
    return create_problem_response(
        status=500,
        title="Internal Server Error",
        detail="An unexpected error occurred",
        error_type="https://habittracker.com/errors/internal-error",
        error_code="INTERNAL_ERROR",
        instance=request.url.path,
    )
