"""
CSRF middleware (double-submit cookie pattern).

Проверка только для авторизованных запросов (есть cookie access_token).
На state-changing методах (POST/PUT/PATCH/DELETE) header X-CSRF-Token
должен совпадать с cookie csrf_token.

Эндпоинты /token и /refresh исключены — они выдают cookies, а не используют их.
"""
import hmac
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
EXEMPT_PATHS = {"/token", "/refresh", "/register/"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path

        if method in UNSAFE_METHODS and path not in EXEMPT_PATHS:
            if request.cookies.get("access_token"):
                cookie_csrf = request.cookies.get("csrf_token")
                header_csrf = request.headers.get("X-CSRF-Token")
                if not cookie_csrf or not header_csrf or not hmac.compare_digest(cookie_csrf, header_csrf):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF token missing or invalid"},
                    )

        return await call_next(request)
