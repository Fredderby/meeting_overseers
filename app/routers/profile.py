import os
import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.authentication.auth import get_current_user, hash_password, verify_password
from app.models.user import User
from app.services.audit_service import create_log
from app.utilities.helpers import get_client_ip
from app.config import settings

router = APIRouter(prefix="", tags=["profile"])


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    user_data = get_current_user(request)
    user = db.query(User).filter(User.id == user_data.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404)
    return HTMLResponse(_profile_html(user))


@router.post("/api/profile/update")
async def update_profile(
    request: Request,
    full_name: str = Form(""),
    email: str = Form(""),
    db: Session = Depends(get_db),
):
    user_data = get_current_user(request)
    user = db.query(User).filter(User.id == user_data.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404)
    if full_name:
        user.full_name = full_name
    if email:
        user.email = email
    db.commit()
    create_log(db, user.id, "update_profile", "Profile", details="Profile updated", ip_address=get_client_ip(request))
    return {"success": True}


@router.post("/api/profile/password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    user_data = get_current_user(request)
    user = db.query(User).filter(User.id == user_data.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404)
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user.password_hash = hash_password(new_password)
    db.commit()
    create_log(db, user.id, "change_password", "Profile", details="Password changed", ip_address=get_client_ip(request))
    return {"success": True}


@router.post("/api/profile/picture")
async def upload_picture(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user_data = get_current_user(request)
    user = db.query(User).filter(User.id == user_data.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404)
    ext = os.path.splitext(file.filename or "pic.jpg")[1]
    filename = f"profile_{user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join("app", "static", "images", filename)
    with open(filepath, "wb") as f:
        f.write(file.file.read())
    user.profile_picture = f"/static/images/{filename}"
    db.commit()
    return {"success": True, "url": user.profile_picture}


def _profile_html(user):
    name = user.full_name or user.username
    email = user.email or ""
    is_admin = user.role == "Administrator"
    admin_nav = ""
    if is_admin:
        admin_nav = """
      <a href="/settings" class="nav-item"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.488.488 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2z"/></svg><span>Settings</span></a>"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Profile | Attendance Verification</title>
<link rel="stylesheet" href="/static/css/dashboard.css">
<link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
<div class="app-container">
  <aside class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-logo"><svg viewBox="0 0 24 24" width="32" height="32"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg><span>DCLM</span></div>
      <button class="sidebar-toggle" id="sidebarToggle"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg></button>
    </div>
    <nav class="sidebar-nav">
      <a href="/dashboard" class="nav-item"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg><span>Dashboard</span></a>
      <a href="/people" class="nav-item"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg><span>People</span></a>
      <a href="/attendance" class="nav-item"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M9 10.09l2.59 2.59L14.59 9.91 16 11.33l-4.41 4.42L7.59 11.5 9 10.09zM19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/></svg><span>Attendance</span></a>
      <a href="/analytics" class="nav-item"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg><span>Analytics</span></a>
      <div class="nav-divider"></div>
      <a href="/upload" class="nav-item"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z"/></svg><span>Upload Data</span></a>
      <a href="/audit-logs" class="nav-item"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg><span>Audit Logs</span></a>
      {admin_nav}
    </nav>
    <div class="sidebar-footer">
      <a href="/profile" class="nav-item active"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg><span>Profile</span></a>
      <form method="post" action="/api/auth/logout" style="display:contents"><button type="submit" class="nav-item logout-btn"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg><span>Logout</span></button></form>
    </div>
  </aside>
<div class="sidebar-backdrop" id="sidebarBackdrop"></div>
<script>
function toggleSidebar() {{
  var s=document.getElementById('sidebar'),b=document.getElementById('sidebarBackdrop');
  if(s){{s.classList.toggle('open');if(b)b.classList.toggle('show');}}
}}
document.addEventListener('DOMContentLoaded', function() {{
  var b=document.getElementById('sidebarBackdrop');
  if(b){{b.addEventListener('click',function(){{var s=document.getElementById('sidebar');if(s)s.classList.remove('open');b.classList.remove('show');}});}}
}});
</script>
  <main class="main-content">
    <header class="topbar">
      <div class="topbar-left">
        <button class="hamburger-btn" id="hamburgerBtn" onclick="toggleSidebar()">
          <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
        </button>
        <h2>My Profile</h2>
      </div>
      <div class="topbar-right">
        <div class="user-badge"><span class="user-avatar">{user.username[0].upper()}</span><span class="user-name">{name}</span></div>
      </div>
    </header>
    <div class="content-area">
      <div class="profile-grid">
        <div class="profile-card">
          <div class="profile-pic-section">
            <div class="profile-pic" id="profilePic">
              <span>{user.username[0].upper()}</span>
            </div>
            <form id="picForm"><input type="file" id="picInput" accept="image/*" hidden onchange="uploadPic(event)"><button type="button" class="btn btn-sm" onclick="document.getElementById('picInput').click()">Change Photo</button></form>
          </div>
          <h3>{name}</h3>
          <p class="profile-role">{user.role}</p>
        </div>
        <div class="profile-form-card">
          <h3>Account Information</h3>
          <form id="profileForm" onsubmit="updateProfile(event)">
            <label>Username</label>
            <input type="text" value="{user.username}" disabled class="input-disabled">
            <label>Full Name</label>
            <input type="text" name="full_name" value="{name}" placeholder="Your full name">
            <label>Email</label>
            <input type="email" name="email" value="{email}" placeholder="your@email.com">
            <button type="submit" class="btn btn-primary">Save Changes</button>
          </form>
        </div>
        <div class="profile-form-card">
          <h3>Change Password</h3>
          <form id="passwordForm" onsubmit="changePassword(event)">
            <label>Current Password</label>
            <input type="password" name="current_password" required>
            <label>New Password</label>
            <input type="password" name="new_password" required minlength="6">
            <label>Confirm Password</label>
            <input type="password" name="confirm_password" required minlength="6">
            <button type="submit" class="btn btn-primary">Update Password</button>
          </form>
        </div>
      </div>
    </div>
  </main>
</div>
<script src="/static/js/profile.js"></script>
</body>
</html>"""
