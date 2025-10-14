from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["50/minute"])


def init_rate_limiting(app):
    """
    Инициализация Rate Limiting для FastAPI приложения.
    Применяет глобальный лимит и кастомный обработчик ошибок.
    """

    app.state.limiter = limiter  # Подключаем лимитер к приложению

    # Кастомный обработчик RateLimitExceeded с JSON-ответом
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "rate_limit",
                    "message": "Too many requests. Try again later.",
                }
            },
        )

    return app
