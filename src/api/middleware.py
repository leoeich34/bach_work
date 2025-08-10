from __future__ import annotations
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """Логируем время обработки запроса и пишем заголовок X-Process-Time-ms"""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1_000
        logger.info("%s %s → %.1f ms", request.method, request.url.path, duration_ms)
        response.headers["X-Process-Time-ms"] = f"{duration_ms:.1f}"
        return response