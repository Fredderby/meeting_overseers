from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Response
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.authentication.auth import (
    verify_password, create_session_token,
    get_current_user, generate_csrf_token,
)
from app.models.user import User
from app.config import settings
from app.utilities.helpers import get_client_ip

router = APIRouter(prefix="", tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return HTMLResponse(_login_html())


@router.post("/api/auth/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        from app.models.audit_log import AuditLog
        db.add(AuditLog(action="login_failed", username=username, details="Invalid credentials", ip_address=get_client_ip(request)))
        db.commit()
        return JSONResponse(status_code=401, content={"error": "Invalid credentials"})

    if not user.is_active:
        return JSONResponse(status_code=403, content={"error": "Account is deactivated"})

    token = create_session_token(user.id, user.username, user.role)
    user.last_login = datetime.utcnow()
    from app.models.audit_log import AuditLog
    db.add(AuditLog(user_id=user.id, username=user.username, action="login", details="User logged in", ip_address=get_client_ip(request)))
    db.commit()

    max_age = 30 * 24 * 60 * 60 if remember_me else settings.SESSION_EXPIRE_MINUTES * 60
    response.set_cookie(
        key="session_token",
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=False,
    )

    return {"success": True, "redirect": "/dashboard"}


@router.post("/api/auth/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_token")
    return response


@router.get("/api/auth/me")
async def get_me(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/api/auth/csrf")
async def get_csrf():
    token = generate_csrf_token()
    return {"csrf_token": token}


def _login_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Login | Attendance Verification System</title>
<link rel="stylesheet" href="/static/css/login.css">
</head>
<body>
<div class="particles" id="particles"></div>
<div class="login-container">
  <div class="login-card">
    <div class="logo-section">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24" width="48" height="48">
          <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        </svg>
      </div>
      <h1>Attendance Verification</h1>
      <p>Sign in to your account</p>
    </div>
    <form id="loginForm" class="login-form" autocomplete="off">
      <div class="input-group">
        <div class="input-icon">
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
        </div>
        <input type="text" id="username" name="username" placeholder="Username" required autofocus>
      </div>
      <div class="input-group">
        <div class="input-icon">
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1s3.1 1.39 3.1 3.1v2z"/>
          </svg>
        </div>
        <input type="password" id="password" name="password" placeholder="Password" required>
        <button type="button" class="toggle-password" id="togglePassword" aria-label="Toggle password visibility">
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
          </svg>
        </button>
      </div>
      <div class="form-options">
        <label class="checkbox-container">
          <input type="checkbox" id="rememberMe" name="remember_me">
          <span class="checkmark"></span>
          Remember Me
        </label>
        <a href="#" class="forgot-link">Forgot Password?</a>
      </div>
      <button type="submit" class="login-btn" id="loginBtn">
        <span class="btn-text">Sign In</span>
        <div class="spinner" id="spinner"></div>
      </button>
      <div id="errorMessage" class="error-message"></div>
    </form>
  </div>
</div>
<script src="/static/js/login.js"></script>
</body>
</html>"""
