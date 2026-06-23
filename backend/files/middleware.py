import time

from django.conf import settings
from django.http import HttpResponse

from files.log_config import get_logger
from files.rate_limit import SlidingWindowRateLimiter

logger = get_logger("middleware")
request_logger = get_logger("request")

_limiter: SlidingWindowRateLimiter | None = None


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.META.get("REMOTE_ADDR") or "unknown")[:64]


def _rate_limit_key(request) -> str | None:
    user_id = request.headers.get("UserId") or request.META.get("HTTP_USERID")
    if user_id:
        return f"user:{user_id.strip()}"
    return f"ip:{_client_ip(request)}"


def get_rate_limiter() -> SlidingWindowRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = SlidingWindowRateLimiter(
            max_calls=getattr(settings, "RATE_LIMIT_CALLS", 2),
            window_seconds=float(getattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 1)),
        )
    return _limiter


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.path_prefix = getattr(settings, "RATE_LIMIT_PATH_PREFIX", "/api/")

    def __call__(self, request):
        if request.path.startswith(self.path_prefix):
            key = _rate_limit_key(request)
            if key and not get_rate_limiter().is_allowed(key):
                logger.warning(
                    "rate_limit_exceeded key=%s method=%s path=%s",
                    key,
                    request.method,
                    request.path,
                )
                return HttpResponse(
                    "Call Limit Reached",
                    status=429,
                    content_type="text/plain",
                )
        return self.get_response(request)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.path_prefix = getattr(settings, "RATE_LIMIT_PATH_PREFIX", "/api/")

    def __call__(self, request):
        if not request.path.startswith(self.path_prefix):
            return self.get_response(request)

        start = time.monotonic()
        user_id = request.headers.get("UserId") or request.META.get("HTTP_USERID") or "-"
        query = request.META.get("QUERY_STRING", "")

        request_logger.info(
            "request_started method=%s path=%s user_id=%s query=%s",
            request.method,
            request.path,
            user_id,
            query or "-",
        )

        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000
        log_fn = request_logger.warning if response.status_code >= 400 else request_logger.info
        log_fn(
            "request_completed method=%s path=%s user_id=%s status=%s duration_ms=%.2f",
            request.method,
            request.path,
            user_id,
            response.status_code,
            duration_ms,
        )
        return response
