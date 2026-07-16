from datetime import datetime, timedelta
from typing import Dict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from app.authentication.auth import get_current_user


def _add_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"


class AppMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path.startswith("/static"):
            response = await call_next(request)
            _add_headers(response)
            return response

        client_ip = request.client.host if request.client else "unknown"
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)

        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(status_code=429, detail="Too many requests")

        self.requests[client_ip].append(now)

        user = None
        token = request.cookies.get("session_token")
        if token:
            user = get_current_user(request)

        if not user and path != "/login" and not path.startswith("/api/"):
            return RedirectResponse(url="/login", status_code=303)

        if user and path == "/login":
            return RedirectResponse(url="/dashboard", status_code=303)

        response = await call_next(request)
        _add_headers(response)
        return response
