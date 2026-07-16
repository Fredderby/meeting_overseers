from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.authentication.auth import get_current_user
from app.services.attendance_service import (
    verify_attendance, get_today_attendance,
    get_unverified_persons, get_attendance_history,
)
from app.services.audit_service import create_log
from app.utilities.helpers import get_client_ip
from app.routers.people import _sidebar_html

router = APIRouter(prefix="", tags=["attendance"])


@router.get("/attendance", response_class=HTMLResponse)
async def attendance_page(
    request: Request,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    unverified = get_unverified_persons(db, category=category)
    today_records, total = get_today_attendance(db, category=category)
    return HTMLResponse(_attendance_html(user, unverified, today_records, category))

@router.post("/api/attendance/verify")
async def verify_person(
    request: Request,
    person_id: int = Form(...),
    remarks: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        att = verify_attendance(
            db, person_id,
            verified_by=user.get("user_id"),
            verified_by_name=user.get("username"),
            remarks=remarks.strip() or None,
        )
        create_log(db, user.get("user_id"), "verify", "Attendance", att.id, f"Verified attendance: {att.person_name}", get_client_ip(request))
        return {"success": True, "person_name": att.person_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/attendance/today")
async def get_today_api(
    request: Request,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    records, total = get_today_attendance(db, category=category)
    return {
        "records": [
            {
                "id": r.id,
                "person_id": r.person_id,
                "person_name": r.person_name,
                "gender": r.gender or "",
                "designation": r.designation or "",
                "category": r.category or "",
                "verification_time": r.verification_time.isoformat() if r.verification_time else "",
                "verified_by_name": r.verified_by_name or "",
                "remarks": r.remarks or "",
            }
            for r in records
        ],
        "total": total,
    }

@router.get("/api/attendance/history")
async def get_history_api(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    records, total = get_attendance_history(db, skip=skip, limit=limit, category=category)
    return {
        "records": [
            {
                "id": r.id,
                "person_id": r.person_id,
                "person_name": r.person_name,
                "gender": r.gender or "",
                "designation": r.designation or "",
                "category": r.category or "",
                "verification_time": r.verification_time.isoformat() if r.verification_time else "",
                "verified_by_name": r.verified_by_name or "",
            }
            for r in records
        ],
        "total": total,
    }


def _attendance_html(user, unverified, today_records, category):
    name = user.get("username", "User")
    cats = ["", "Men", "Women", "Stakeholders"]
    cat_labels = {"": "All", "Men": "Men", "Women": "Women", "Stakeholders": "Stakeholders"}
    tabs = ""
    for c in cats:
        active_tab = 'active' if (category == c or (not category and not c)) else ''
        href = f"/attendance?category={c}" if c else "/attendance"
        tabs += f'<button class="tab-btn {active_tab}" onclick="window.location.href=\'{href}\'">{cat_labels[c]}</button>'

    verified_rows = ""
    for r in today_records:
        verified_rows += f"""
        <tr>
          <td>{r.person_name}</td>
          <td>{r.gender or '-'}</td>
          <td>{r.designation or '-'}</td>
          <td>{r.category or '-'}</td>
          <td>{r.verification_time.strftime('%I:%M %p') if r.verification_time else '-'}</td>
          <td>{r.verified_by_name or '-'}</td>
        </tr>"""

    unverified_cards = ""
    for p in unverified:
        unverified_cards += f"""
        <div class="person-card" data-id="{p.id}" data-name="{p.name.replace("'", "\\'")}">
          <div class="person-info">
            <strong>{p.name}</strong>
            <span class="text-muted">{p.gender or ''} | {p.designation or ''} | {p.category or ''}</span>
          </div>
          <button class="btn btn-success btn-sm verify-btn" onclick="verifyPerson({p.id}, '{p.name.replace("'", "\\'")}')">Mark Present</button>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Attendance | Verification System</title>
<link rel="stylesheet" href="/static/css/dashboard.css">
<link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
<div class="app-container">
  {_sidebar_html(user, 'attendance')}
  <main class="main-content">
    <header class="topbar">
      <div class="topbar-left"><h2>Attendance Verification</h2></div>
      <div class="topbar-right">
        <div class="user-badge"><span class="user-avatar">{name[0].upper()}</span><span class="user-name">{name}</span></div>
      </div>
    </header>
    <div class="content-area">
      <div class="attendance-grid">
        <div class="card">
          <div class="card-header"><h3>Unverified Persons</h3>
            <input type="text" id="verifySearch" placeholder="Search..." onkeyup="filterUnverified(this.value)">
          </div>
          <div class="tabs" style="padding:0 1rem">{tabs}</div>
          <div id="unverifiedList" class="person-list">
            {unverified_cards or '<p class="empty-state">All persons have been verified today!</p>'}
          </div>
        </div>
        <div class="card">
          <div class="card-header"><h3>Today's Verification Log</h3><span class="badge badge-info">{len(today_records)} verified</span></div>
          <div class="table-wrapper">
            <table class="data-table">
              <thead><tr><th>Name</th><th>Gender</th><th>Designation</th><th>Category</th><th>Time</th><th>Verified By</th></tr></thead>
              <tbody>{verified_rows or '<tr><td colspan="6" class="empty-row">No verifications yet today</td></tr>'}</tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </main>
</div>

<div class="modal" id="verifyModal">
  <div class="modal-overlay" onclick="closeVerifyModal()"></div>
  <div class="modal-content modal-sm">
    <div class="modal-header">
      <h3>Confirm Verification</h3>
      <button class="modal-close" onclick="closeVerifyModal()">&times;</button>
    </div>
    <form id="verifyForm" onsubmit="confirmVerify(event)">
      <input type="hidden" id="verifyPersonId" value="">
      <p id="verifyPersonName" style="padding:0 1rem"></p>
      <div class="form-group" style="padding:0 1rem 1rem">
        <label>Remarks (optional)</label>
        <textarea id="verifyRemarks" rows="2"></textarea>
      </div>
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" onclick="closeVerifyModal()">Cancel</button>
        <button type="submit" class="btn btn-success" id="verifyBtn">Verify</button>
      </div>
    </form>
  </div>
</div>

<script>
let verifyData = {{}};
function verifyPerson(id, name) {{
  verifyData.id = id;
  verifyData.name = name;
  document.getElementById('verifyPersonId').value = id;
  document.getElementById('verifyPersonName').textContent = `Verify attendance for: ${{name}}`;
  document.getElementById('verifyRemarks').value = '';
  document.getElementById('verifyModal').classList.add('open');
}}
function closeVerifyModal() {{ document.getElementById('verifyModal').classList.remove('open'); }}
function confirmVerify(e) {{
  e.preventDefault();
  const fd = new FormData();
  fd.append('person_id', document.getElementById('verifyPersonId').value);
  fd.append('remarks', document.getElementById('verifyRemarks').value);
  const btn = document.getElementById('verifyBtn');
  btn.disabled = true; btn.textContent = 'Verifying...';
  fetch('/api/attendance/verify', {{ method:'POST', body: fd }})
    .then(r => r.json())
    .then(d => {{ if(d.success) {{ closeVerifyModal(); location.reload(); }} else {{ alert('Error: '+d.error); }} }})
    .catch(e => alert('Error: '+e))
    .finally(() => {{ btn.disabled = false; btn.textContent = 'Verify'; }});
}}
function filterUnverified(val) {{
  const cards = document.querySelectorAll('.person-card');
  const q = val.toLowerCase();
  cards.forEach(c => {{
    const name = c.querySelector('strong').textContent.toLowerCase();
    c.style.display = name.includes(q) ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""
