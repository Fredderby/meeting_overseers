from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, Response
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="auth-session")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_session_token(user_id: int, username: str, role: str) -> str:
    data = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "iat": datetime.utcnow().isoformat(),
    }
    return serializer.dumps(data)


def decode_session_token(token: str) -> Optional[dict]:
    try:
        data = serializer.loads(token, max_age=settings.SESSION_EXPIRE_MINUTES * 60)
        return data
    except (BadSignature, SignatureExpired):
        return None


def get_current_user(request: Request) -> Optional[dict]:
    if hasattr(request.state, "user"):
        return request.state.user
    token = request.cookies.get("session_token")
    if not token:
        return None
    data = decode_session_token(token)
    if not data:
        return None
    request.state.user = data
    return data


def require_auth(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


def require_admin(request: Request):
    user = require_auth(request)
    if user.get("role") != "Administrator":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


def generate_csrf_token() -> str:
    s = URLSafeTimedSerializer(settings.SECRET_KEY, salt="csrf")
    return s.dumps({"csrf": "token"})


def verify_csrf_token(token: str) -> bool:
    s = URLSafeTimedSerializer(settings.SECRET_KEY, salt="csrf")
    try:
        s.loads(token, max_age=3600)
        return True
    except (BadSignature, SignatureExpired):
        return False
