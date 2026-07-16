from typing import Optional
from datetime import date
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.authentication.auth import get_current_user
from app.services.audit_service import get_logs
from app.routers.people import _sidebar_html

router = APIRouter(prefix="", tags=["audit"])


@router.get("/audit-logs", response_class=HTMLResponse)
async def audit_page(
    request: Request,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    limit = 100
    skip = (page - 1) * limit
    logs, total = get_logs(db, skip=skip, limit=limit, action=action, entity_type=entity_type)
    total_pages = max(1, (total + limit - 1) // limit)
    return HTMLResponse(_audit_html(user, logs, total, page, total_pages, action, entity_type))


@router.get("/api/audit-logs")
async def audit_api(
    request: Request,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    skip = (page - 1) * limit
    logs, total = get_logs(db, skip=skip, limit=limit, action=action, entity_type=entity_type)
    return {
        "logs": [
            {
                "id": l.id,
                "user_id": l.user_id,
                "username": l.username or "",
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "details": l.details or "",
                "ip_address": l.ip_address or "",
                "timestamp": l.timestamp.isoformat() if l.timestamp else "",
            }
            for l in logs
        ],
        "total": total,
        "page": page,
        "total_pages": max(1, (total + limit - 1) // limit),
    }


def _audit_html(user, logs, total, page, total_pages, action_filter, entity_filter):
    name = user.get("username", "User")
    rows = ""
    for l in logs:
        rows += f"""
        <tr>
          <td>{l.timestamp.strftime('%Y-%m-%d %H:%M') if l.timestamp else '-'}</td>
          <td>{l.username or '-'}</td>
          <td><span class="badge badge-{l.action}">{l.action}</span></td>
          <td>{l.entity_type or '-'}</td>
          <td>{l.entity_id or '-'}</td>
          <td>{l.details or '-'}</td>
          <td>{l.ip_address or '-'}</td>
        </tr>"""

    pagination = ""
    if total_pages > 1:
        pagination += '<div class="pagination">'
        if page > 1:
            pagination += f'<a href="?page={page-1}&action={action_filter or ""}&entity_type={entity_filter or ""}" class="page-link">&laquo;</a>'
        for p in range(1, total_pages + 1):
            active = 'active' if p == page else ''
            pagination += f'<a href="?page={p}&action={action_filter or ""}&entity_type={entity_filter or ""}" class="page-link {active}">{p}</a>'
        if page < total_pages:
            pagination += f'<a href="?page={page+1}&action={action_filter or ""}&entity_type={entity_filter or ""}" class="page-link">&raquo;</a>'
        pagination += '</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Audit Logs | Attendance Verification</title>
<link rel="stylesheet" href="/static/css/dashboard.css">
<link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
<div class="app-container">
  {_sidebar_html(user, 'audit')}
  <main class="main-content">
    <header class="topbar">
      <div class="topbar-left">
        <button class="hamburger-btn" id="hamburgerBtn" onclick="toggleSidebar()">
          <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
        </button>
        <h2>Audit Logs</h2>
      </div>
      <div class="topbar-right">
        <div class="user-badge"><span class="user-avatar">{name[0].upper()}</span><span class="user-name">{name}</span></div>
      </div>
    </header>
    <div class="content-area">
      <div class="card">
        <div class="card-header">
          <div class="filter-group">
            <select id="actionFilter" onchange="applyFilter()">
              <option value="">All Actions</option>
              <option value="login" {"selected" if action_filter=="login" else ""}>Login</option>
              <option value="create" {"selected" if action_filter=="create" else ""}>Create</option>
              <option value="update" {"selected" if action_filter=="update" else ""}>Update</option>
              <option value="delete" {"selected" if action_filter=="delete" else ""}>Delete</option>
              <option value="verify" {"selected" if action_filter=="verify" else ""}>Verify</option>
            </select>
            <span class="badge badge-info">{total} total</span>
          </div>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead><tr><th>Timestamp</th><th>User</th><th>Action</th><th>Entity</th><th>Entity ID</th><th>Details</th><th>IP Address</th></tr></thead>
            <tbody>{rows or '<tr><td colspan="7" class="empty-row">No audit logs found</td></tr>'}</tbody>
          </table>
        </div>
        {pagination}
      </div>
    </div>
  </main>
</div>
<script>
function applyFilter() {{
  const action = document.getElementById('actionFilter').value;
  window.location.href = `/audit-logs?action=${{action}}`;
}}
</script>
</body>
</html>"""
