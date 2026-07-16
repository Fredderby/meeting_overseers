from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.authentication.auth import get_current_user, hash_password
from app.services.user_service import (
    get_users, get_user, get_user_by_username,
    create_user, update_user, reset_password, delete_user, get_user_stats,
)
from app.services.audit_service import create_log
from app.utilities.helpers import get_client_ip

router = APIRouter(prefix="", tags=["settings"])


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    if user.get("role") != "Administrator":
        raise HTTPException(status_code=403, detail="Administrator access required")
    limit = 20
    skip = (page - 1) * limit
    users, total = get_users(db, skip=skip, limit=limit, search=search)
    total_pages = max(1, (total + limit - 1) // limit)
    stats = get_user_stats(db)
    return HTMLResponse(_settings_html(user, users, total, page, total_pages, search, stats))


@router.get("/api/users")
async def list_users_api(
    request: Request,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user or user.get("role") != "Administrator":
        raise HTTPException(status_code=403, detail="Admin only")
    skip = (page - 1) * limit
    users, total = get_users(db, skip=skip, limit=limit, search=search)
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name or "",
                "email": u.email or "",
                "role": u.role,
                "is_active": u.is_active,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "total_pages": max(1, (total + limit - 1) // limit),
    }


@router.post("/api/users")
async def add_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    email: str = Form(""),
    role: str = Form("Verifier"),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user or user.get("role") != "Administrator":
        raise HTTPException(status_code=403, detail="Admin only")
    if get_user_by_username(db, username.strip()):
        return JSONResponse(status_code=400, content={"error": "Username already exists"})
    if len(password.strip()) < 4:
        return JSONResponse(status_code=400, content={"error": "Password must be at least 4 characters"})
    new_user = create_user(db, username.strip(), password.strip(), full_name, email, role)
    create_log(db, user.get("user_id"), "create", "User", new_user.id, f"Created user: {new_user.username}", get_client_ip(request))
    return {"success": True, "user_id": new_user.id}


@router.put("/api/users/{user_id}")
async def edit_user(
    request: Request,
    user_id: int,
    full_name: str = Form(""),
    email: str = Form(""),
    role: str = Form("Verifier"),
    is_active: str = Form("true"),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user or user.get("role") != "Administrator":
        raise HTTPException(status_code=403, detail="Admin only")
    updated = update_user(db, user_id, full_name=full_name, email=email, role=role, is_active=(is_active == "true"))
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    create_log(db, user.get("user_id"), "update", "User", user_id, f"Updated user: {updated.username}", get_client_ip(request))
    return {"success": True}


@router.post("/api/users/{user_id}/reset-password")
async def reset_user_password(
    request: Request,
    user_id: int,
    new_password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user or user.get("role") != "Administrator":
        raise HTTPException(status_code=403, detail="Admin only")
    if len(new_password.strip()) < 4:
        return JSONResponse(status_code=400, content={"error": "Password must be at least 4 characters"})
    updated = reset_password(db, user_id, new_password.strip())
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    create_log(db, user.get("user_id"), "update", "User", user_id, f"Reset password for: {updated.username}", get_client_ip(request))
    return {"success": True}


@router.delete("/api/users/{user_id}")
async def remove_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.get("role") != "Administrator":
        raise HTTPException(status_code=403, detail="Admin only")
    target = get_user(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == user.get("user_id"):
        return JSONResponse(status_code=400, content={"error": "Cannot delete your own account"})
    name = target.username
    delete_user(db, user_id)
    create_log(db, user.get("user_id"), "delete", "User", user_id, f"Deleted user: {name}", get_client_ip(request))
    return {"success": True}


def _sidebar_html(user, active="settings"):
    name = user.get("username", "User")
    is_admin = user.get("role") == "Administrator"
    admin_nav = ""
    if is_admin:
        admin_nav = f"""
    <a href="/settings" class="nav-item {'active' if active=='settings' else ''}"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.488.488 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2z"/></svg><span>Settings</span></a>"""
    return f"""
<aside class="sidebar" id="sidebar">
  <div class="sidebar-header">
    <div class="sidebar-logo"><svg viewBox="0 0 24 24" width="32" height="32"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg><span>DCLM</span></div>
    <button class="sidebar-toggle" id="sidebarToggle"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg></button>
  </div>
  <nav class="sidebar-nav">
    <a href="/dashboard" class="nav-item {'active' if active=='dashboard' else ''}"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg><span>Dashboard</span></a>
    <a href="/people" class="nav-item {'active' if active=='people' else ''}"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg><span>People</span></a>
    <a href="/attendance" class="nav-item {'active' if active=='attendance' else ''}"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M9 10.09l2.59 2.59L14.59 9.91 16 11.33l-4.41 4.42L7.59 11.5 9 10.09zM19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/></svg><span>Attendance</span></a>
    <a href="/analytics" class="nav-item {'active' if active=='analytics' else ''}"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg><span>Analytics</span></a>
    <div class="nav-divider"></div>
    <a href="/upload" class="nav-item {'active' if active=='upload' else ''}"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z"/></svg><span>Upload Data</span></a>
    <a href="/audit-logs" class="nav-item {'active' if active=='audit' else ''}"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg><span>Audit Logs</span></a>
    {admin_nav}
  </nav>
  <div class="sidebar-footer">
    <a href="/profile" class="nav-item"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg><span>Profile</span></a>
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
</script>"""


def _settings_html(user, users, total, page, total_pages, search, stats):
    name = user.get("username", "User")
    rows = ""
    for u in users:
        status_badge = '<span class="badge badge-men">Active</span>' if u.is_active else '<span class="badge badge-women">Inactive</span>'
        role_badge = '<span class="badge badge-stake">Admin</span>' if u.role == "Administrator" else '<span class="badge badge-men">Verifier</span>'
        last = u.last_login.strftime("%d %b %Y %H:%M") if u.last_login else "Never"
        rows += f"""
        <tr>
          <td><strong>{u.username}</strong></td>
          <td>{u.full_name or '-'}</td>
          <td>{u.email or '-'}</td>
          <td>{role_badge}</td>
          <td>{status_badge}</td>
          <td>{last}</td>
          <td class="action-cell">
            <button class="btn btn-sm btn-icon edit-btn" onclick="editUser({u.id}, '{u.username}', '{(u.full_name or '').replace("'", "\\'")}', '{(u.email or '').replace("'", "\\'")}', '{u.role}', {str(u.is_active).lower()})" title="Edit"><svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg></button>
            <button class="btn btn-sm btn-icon" onclick="resetPassword({u.id}, '{u.username}')" title="Reset Password"><svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1s3.1 1.39 3.1 3.1v2z"/></svg></button>
            <button class="btn btn-sm btn-icon delete-btn" onclick="deleteUser({u.id}, '{u.username}')" title="Delete"><svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg></button>
          </td>
        </tr>"""

    pagination = ""
    import urllib.parse
    search_param = urllib.parse.quote(search or "")
    if total_pages > 1:
        pagination += '<div class="pagination">'
        if page > 1:
            pagination += f'<a href="?page={page-1}&search={search_param}" class="page-link">&laquo;</a>'
        for p in range(1, total_pages + 1):
            active = 'active' if p == page else ''
            pagination += f'<a href="?page={p}&search={search_param}" class="page-link {active}">{p}</a>'
        if page < total_pages:
            pagination += f'<a href="?page={page+1}&search={search_param}" class="page-link">&raquo;</a>'
        pagination += '</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Settings | DCLM Attendance</title>
<link rel="stylesheet" href="/static/css/dashboard.css">
<link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
<div class="app-container">
  {_sidebar_html(user, 'settings')}
  <main class="main-content">
    <header class="topbar">
      <div class="topbar-left">
        <button class="hamburger-btn" id="hamburgerBtn" onclick="toggleSidebar()">
          <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
        </button>
        <h2>User Management</h2>
      </div>
      <div class="topbar-right">
        <div class="search-box">
          <input type="text" id="searchInput" placeholder="Search users..." value="{search or ''}" onkeyup="if(event.key==='Enter')searchUsers()">
          <button onclick="searchUsers()"><svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg></button>
        </div>
        <div class="user-badge"><span class="user-avatar">{name[0].upper()}</span><span class="user-name">{name}</span></div>
      </div>
    </header>
    <div class="content-area">
      <div class="stats-grid" style="margin-bottom:1.5rem">
        <div class="stat-card"><div class="stat-value">{stats['total']}</div><div class="stat-label">Total Users</div></div>
        <div class="stat-card"><div class="stat-value">{stats['active']}</div><div class="stat-label">Active</div></div>
        <div class="stat-card"><div class="stat-value">{stats['admins']}</div><div class="stat-label">Admins</div></div>
        <div class="stat-card"><div class="stat-value">{stats['verifiers']}</div><div class="stat-label">Verifiers</div></div>
      </div>
      <div class="card">
        <div class="card-header">
          <h3 style="margin:0">Users</h3>
          <button class="btn btn-primary" onclick="showAddModal()">+ Add User</button>
        </div>
        <div class="table-wrapper">
          <table class="data-table" id="usersTable">
            <thead>
              <tr><th>Username</th><th>Full Name</th><th>Email</th><th>Role</th><th>Status</th><th>Last Login</th><th>Actions</th></tr>
            </thead>
            <tbody>{rows or '<tr><td colspan="7" class="empty-row">No users found</td></tr>'}</tbody>
          </table>
        </div>
        {pagination}
      </div>
    </div>
  </main>
</div>

<div class="modal" id="userModal">
  <div class="modal-overlay" onclick="closeModal()"></div>
  <div class="modal-content">
    <div class="modal-header">
      <h3 id="modalTitle">Add User</h3>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <form id="userForm" onsubmit="saveUser(event)">
      <input type="hidden" id="userId" value="">
      <div class="form-grid">
        <div class="form-group">
          <label>Username *</label>
          <input type="text" id="uUsername" required>
        </div>
        <div class="form-group" id="passwordGroup">
          <label>Password *</label>
          <input type="password" id="uPassword" required minlength="4">
        </div>
        <div class="form-group">
          <label>Full Name</label>
          <input type="text" id="uFullName">
        </div>
        <div class="form-group">
          <label>Email</label>
          <input type="email" id="uEmail">
        </div>
        <div class="form-group">
          <label>Role</label>
          <select id="uRole">
            <option value="Verifier">Verifier</option>
            <option value="Administrator">Administrator</option>
          </select>
        </div>
        <div class="form-group" id="activeGroup" style="display:none">
          <label>Status</label>
          <select id="uActive">
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
      </div>
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary" id="saveBtn">Save</button>
      </div>
    </form>
  </div>
</div>

<div class="modal" id="deleteModal">
  <div class="modal-overlay" onclick="closeDeleteModal()"></div>
  <div class="modal-content modal-sm">
    <div class="modal-header">
      <h3>Delete User</h3>
      <button class="modal-close" onclick="closeDeleteModal()">&times;</button>
    </div>
    <p id="deleteMsg" style="padding:1rem">Are you sure?</p>
    <div class="modal-actions">
      <button type="button" class="btn btn-secondary" onclick="closeDeleteModal()">Cancel</button>
      <button type="button" class="btn btn-danger" id="confirmDeleteBtn" onclick="confirmDelete()">Delete</button>
    </div>
  </div>
</div>

<div class="modal" id="resetModal">
  <div class="modal-overlay" onclick="closeResetModal()"></div>
  <div class="modal-content modal-sm">
    <div class="modal-header">
      <h3>Reset Password</h3>
      <button class="modal-close" onclick="closeResetModal()">&times;</button>
    </div>
    <p style="padding:0 1rem 0.5rem">Set new password for <strong id="resetUser"></strong></p>
    <form onsubmit="confirmReset(event)" style="padding:0 1rem 1rem">
      <input type="hidden" id="resetUserId">
      <input type="password" id="newPassword" placeholder="New password" required minlength="4" style="width:100%;padding:0.5rem;border:1px solid #ddd;border-radius:6px;margin-bottom:1rem">
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" onclick="closeResetModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Reset</button>
      </div>
    </form>
  </div>
</div>

<script>
let deleteId = null;
function showAddModal() {{
  document.getElementById('modalTitle').textContent = 'Add User';
  document.getElementById('userId').value = '';
  document.getElementById('userForm').reset();
  document.getElementById('uUsername').disabled = false;
  document.getElementById('passwordGroup').style.display = '';
  document.getElementById('activeGroup').style.display = 'none';
  document.getElementById('userModal').classList.add('open');
}}
function editUser(id, username, fullName, email, role, isActive) {{
  document.getElementById('modalTitle').textContent = 'Edit User';
  document.getElementById('userId').value = id;
  document.getElementById('uUsername').value = username;
  document.getElementById('uUsername').disabled = true;
  document.getElementById('uFullName').value = fullName;
  document.getElementById('uEmail').value = email;
  document.getElementById('uRole').value = role;
  document.getElementById('uActive').value = isActive ? 'true' : 'false';
  document.getElementById('passwordGroup').style.display = 'none';
  document.getElementById('activeGroup').style.display = '';
  document.getElementById('userModal').classList.add('open');
}}
function closeModal() {{ document.getElementById('userModal').classList.remove('open'); }}
function closeDeleteModal() {{ document.getElementById('deleteModal').classList.remove('open'); deleteId = null; }}
function closeResetModal() {{ document.getElementById('resetModal').classList.remove('open'); }}
function saveUser(e) {{
  e.preventDefault();
  const id = document.getElementById('userId').value;
  const data = new FormData();
  data.append('username', document.getElementById('uUsername').value);
  data.append('full_name', document.getElementById('uFullName').value);
  data.append('email', document.getElementById('uEmail').value);
  data.append('role', document.getElementById('uRole').value);
  data.append('is_active', document.getElementById('uActive').value);
  if (!id) {{ data.append('password', document.getElementById('uPassword').value); }}
  const method = id ? 'PUT' : 'POST';
  const url = id ? `/api/users/${{id}}` : '/api/users';
  const btn = document.getElementById('saveBtn');
  btn.disabled = true; btn.textContent = 'Saving...';
  fetch(url, {{ method, body: data }})
    .then(r => r.json())
    .then(d => {{ if(d.success) {{ closeModal(); location.reload(); }} else {{ alert('Error: '+(d.error||'Unknown')); }} }})
    .catch(e => alert('Error: '+e))
    .finally(() => {{ btn.disabled = false; btn.textContent = 'Save'; }});
}}
function deleteUser(id, username) {{
  deleteId = id;
  document.getElementById('deleteMsg').textContent = 'Are you sure you want to delete "'+username+'"?';
  document.getElementById('deleteModal').classList.add('open');
}}
function confirmDelete() {{
  if(!deleteId) return;
  const btn = document.getElementById('confirmDeleteBtn');
  btn.disabled = true; btn.textContent = 'Deleting...';
  fetch(`/api/users/${{deleteId}}`, {{ method: 'DELETE' }})
    .then(r => r.json())
    .then(d => {{ if(d.success) {{ closeDeleteModal(); location.reload(); }} else {{ alert('Error: '+(d.error||'Unknown')); }} }})
    .catch(e => alert('Error: '+e))
    .finally(() => {{ btn.disabled = false; btn.textContent = 'Delete'; deleteId = null; }});
}}
function resetPassword(id, username) {{
  document.getElementById('resetUserId').value = id;
  document.getElementById('resetUser').textContent = username;
  document.getElementById('newPassword').value = '';
  document.getElementById('resetModal').classList.add('open');
}}
function confirmReset(e) {{
  e.preventDefault();
  const id = document.getElementById('resetUserId').value;
  const pw = document.getElementById('newPassword').value;
  const data = new FormData();
  data.append('new_password', pw);
  fetch(`/api/users/${{id}}/reset-password`, {{ method: 'POST', body: data }})
    .then(r => r.json())
    .then(d => {{ if(d.success) {{ closeResetModal(); alert('Password reset successfully'); }} else {{ alert('Error: '+(d.error||'Unknown')); }} }})
    .catch(e => alert('Error: '+e));
}}
function searchUsers() {{
  const q = document.getElementById('searchInput').value;
  const params = new URLSearchParams(window.location.search);
  params.set('search', q);
  params.delete('page');
  window.location.href = '/settings?' + params.toString();
}}
</script>
</body>
</html>"""
