from collections.abc import Awaitable, Callable

from starlette.responses import JSONResponse


MiB = 1024 * 1024

# The small allowance above each file limit covers multipart boundaries and fields.
REQUEST_BODY_LIMITS = {
    ("POST", "/api/zaigong/upload"): 21 * MiB,
    ("POST", "/api/budget/upload"): 21 * MiB,
    ("POST", "/api/archive/upload"): 51 * MiB,
    ("POST", "/api/backup/restore"): 129 * MiB,
}
DEFAULT_WRITE_BODY_LIMIT = 2 * MiB


class RequestBodyTooLarge(Exception):
    pass


class RequestBodyLimitMiddleware:
    """Reject oversized request bodies before multipart parsing or route handling."""

    def __init__(
        self,
        app,
        route_limits: dict[tuple[str, str], int] | None = None,
        default_limit: int = DEFAULT_WRITE_BODY_LIMIT,
    ):
        self.app = app
        self.route_limits = route_limits or REQUEST_BODY_LIMITS
        self.default_limit = default_limit

    async def __call__(self, scope, receive: Callable[[], Awaitable[dict]], send):
        if scope["type"] != "http" or scope.get("method") not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return

        key = (scope["method"], scope.get("path", ""))
        limit = self.route_limits.get(key, self.default_limit)
        headers = {name.lower(): value for name, value in scope.get("headers", [])}
        raw_content_length = headers.get(b"content-length")

        if raw_content_length is not None:
            try:
                content_length = int(raw_content_length)
            except (TypeError, ValueError):
                await JSONResponse(
                    {"success": False, "message": "Content-Length 无效"},
                    status_code=400,
                )(scope, receive, send)
                return
            if content_length < 0:
                await JSONResponse(
                    {"success": False, "message": "Content-Length 无效"},
                    status_code=400,
                )(scope, receive, send)
                return
            if content_length > limit:
                await self._reject(scope, receive, send, limit)
                return

        received = 0
        response_started = False

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise RequestBodyTooLarge
            return message

        async def tracked_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except RequestBodyTooLarge:
            if response_started:
                raise
            await self._reject(scope, receive, send, limit)

    @staticmethod
    async def _reject(scope, receive, send, limit: int):
        await JSONResponse(
            {
                "success": False,
                "message": f"请求内容不能超过 {limit // MiB}MB",
            },
            status_code=413,
        )(scope, receive, send)
