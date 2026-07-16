from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.authentication.auth import get_current_user
from app.services.person_service import (
    get_person, get_persons, create_person,
    update_person, delete_person,
)
from app.services.audit_service import create_log
from app.utilities.helpers import get_client_ip

router = APIRouter(prefix="", tags=["people"])


@router.get("/people", response_class=HTMLResponse)
async def people_page(
    request: Request,
    category: Optional[str] = None,
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    limit = 50
    skip = (page - 1) * limit
    persons, total = get_persons(db, skip=skip, limit=limit, category=category, search=search)
    total_pages = max(1, (total + limit - 1) // limit)
    return HTMLResponse(_people_html(user, persons, total, page, total_pages, category, search))


@router.get("/api/people")
async def get_people_api(
    request: Request,
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    skip = (page - 1) * limit
    persons, total = get_persons(db, skip=skip, limit=limit, category=category, search=search)
    return {
        "persons": [
            {
                "id": p.id,
                "name": p.name,
                "gender": p.gender or "",
                "designation": p.designation or "",
                "phone_number": p.phone_number or "",
                "region_division": p.region_division or "",
                "category": p.category or "",
                "remarks": p.remarks or "",
            }
            for p in persons
        ],
        "total": total,
        "page": page,
        "total_pages": max(1, (total + limit - 1) // limit),
    }


@router.post("/api/people")
async def add_person(
    request: Request,
    name: str = Form(...),
    gender: str = Form(""),
    designation: str = Form(""),
    phone_number: str = Form(""),
    region_division: str = Form(""),
    category: str = Form(""),
    remarks: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    person = create_person(
        db,
        name=name.strip(),
        gender=gender.strip() or None,
        designation=designation.strip() or None,
        phone_number=phone_number.strip() or None,
        region_division=region_division.strip() or None,
        category=category.strip() or None,
        remarks=remarks.strip() or None,
    )
    create_log(db, user.get("user_id"), "create", "Person", person.id, f"Created person: {person.name}", get_client_ip(request))
    return {"success": True, "person": {"id": person.id, "name": person.name}}


@router.put("/api/people/{person_id}")
async def edit_person(
    request: Request,
    person_id: int,
    name: str = Form(...),
    gender: str = Form(""),
    designation: str = Form(""),
    phone_number: str = Form(""),
    region_division: str = Form(""),
    category: str = Form(""),
    remarks: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    person = update_person(
        db, person_id,
        name=name.strip(),
        gender=gender.strip() or None,
        designation=designation.strip() or None,
        phone_number=phone_number.strip() or None,
        region_division=region_division.strip() or None,
        category=category.strip() or None,
        remarks=remarks.strip() or None,
    )
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    create_log(db, user.get("user_id"), "update", "Person", person_id, f"Updated person: {person.name}", get_client_ip(request))
    return {"success": True}


@router.delete("/api/people/{person_id}")
async def remove_person(request: Request, person_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    person = get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    name = person.name
    delete_person(db, person_id)
    create_log(db, user.get("user_id"), "delete", "Person", person_id, f"Deleted person: {name}", get_client_ip(request))
    return {"success": True}


def _sidebar_html(user, active="people"):
    name = user.get("username", "User")
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
  </nav>
  <div class="sidebar-footer">
    <a href="/profile" class="nav-item"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg><span>Profile</span></a>
    <form method="post" action="/api/auth/logout" style="display:contents"><button type="submit" class="nav-item logout-btn"><svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg><span>Logout</span></button></form>
  </div>
</aside>
<div class="sidebar-backdrop" id="sidebarBackdrop"></div>
<script>
document.addEventListener('DOMContentLoaded', function() {{
  var t=document.getElementById('sidebarToggle'),s=document.getElementById('sidebar'),b=document.getElementById('sidebarBackdrop');
  if(t&&s){{t.addEventListener('click',function(){{s.classList.toggle('open');if(b)b.classList.toggle('show');}});}}
  if(b){{b.addEventListener('click',function(){{s.classList.remove('open');b.classList.remove('show');}});}}
}});
</script>"""


def _people_html(user, persons, total, page, total_pages, category, search):
    name = user.get("username", "User")
    cats = ["", "Men", "Women", "Stakeholders"]
    cat_labels = {"": "All", "Men": "Men", "Women": "Women", "Stakeholders": "Stakeholders"}
    rows = ""
    for p in persons:
        rows += f"""
        <tr>
          <td>{p.name}</td>
          <td>{p.gender or '-'}</td>
          <td>{p.designation or '-'}</td>
          <td>{p.phone_number or '-'}</td>
          <td>{p.region_division or '-'}</td>
          <td><span class="badge badge-{'men' if p.category=='Men' else 'women' if p.category=='Women' else 'stake'}">{p.category or '-'}</span></td>
          <td class="action-cell">
            <button class="btn btn-sm btn-icon edit-btn" onclick="editPerson({p.id}, '{p.name.replace("'", "\\'")}', '{p.gender or ''}', '{p.designation or ''}', '{p.phone_number or ''}', '{p.region_division or ''}', '{p.category or ''}', '{p.remarks or ''}')" title="Edit"><svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg></button>
            <button class="btn btn-sm btn-icon delete-btn" onclick="deletePerson({p.id}, '{p.name.replace("'", "\\'")}')" title="Delete"><svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg></button>
          </td>
        </tr>"""

    tabs = ""
    for c in cats:
        active_tab = 'active' if (category == c or (not category and not c)) else ''
        href = f"/people?category={c}" if c else "/people"
        tabs += f'<button class="tab-btn {active_tab}" onclick="window.location.href=\'{href}\'">{cat_labels[c]}</button>'

    pagination = ""
    import urllib.parse
    cat_param = urllib.parse.quote(category or "")
    search_param = urllib.parse.quote(search or "")
    if total_pages > 1:
        pagination += '<div class="pagination">'
        if page > 1:
            pagination += f'<a href="?page={page-1}&category={cat_param}&search={search_param}" class="page-link">&laquo;</a>'
        for p in range(1, total_pages + 1):
            active = 'active' if p == page else ''
            pagination += f'<a href="?page={p}&category={cat_param}&search={search_param}" class="page-link {active}">{p}</a>'
        if page < total_pages:
            pagination += f'<a href="?page={page+1}&category={cat_param}&search={search_param}" class="page-link">&raquo;</a>'
        pagination += '</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>People | Attendance Verification</title>
<link rel="stylesheet" href="/static/css/dashboard.css">
<link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
<div class="app-container">
  {_sidebar_html(user, 'people')}
  <main class="main-content">
    <header class="topbar">
      <div class="topbar-left"><h2>People Management</h2></div>
      <div class="topbar-right">
        <div class="search-box">
          <input type="text" id="searchInput" placeholder="Search..." value="{search or ''}" onkeyup="if(event.key==='Enter')searchPeople()">
          <button onclick="searchPeople()"><svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg></button>
        </div>
        <div class="user-badge"><span class="user-avatar">{name[0].upper()}</span><span class="user-name">{name}</span></div>
      </div>
    </header>
    <div class="content-area">
      <div class="card">
        <div class="card-header">
          <div class="tabs">{tabs}</div>
          <button class="btn btn-primary" onclick="showAddModal()">+ Add Person</button>
        </div>
        <div class="table-wrapper">
          <table class="data-table" id="peopleTable">
            <thead>
              <tr><th>Name</th><th>Gender</th><th>Designation</th><th>Phone</th><th>Region/Division</th><th>Category</th><th>Actions</th></tr>
            </thead>
            <tbody>{rows or '<tr><td colspan="7" class="empty-row">No people found</td></tr>'}</tbody>
          </table>
        </div>
        {pagination}
      </div>
      <div class="card-footer-info">{total} total records</div>
    </div>
  </main>
</div>

<div class="modal" id="personModal">
  <div class="modal-overlay" onclick="closeModal()"></div>
  <div class="modal-content">
    <div class="modal-header">
      <h3 id="modalTitle">Add Person</h3>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <form id="personForm" onsubmit="savePerson(event)">
      <input type="hidden" id="personId" value="">
      <div class="form-grid">
        <div class="form-group">
          <label>Name *</label>
          <input type="text" id="pName" required>
        </div>
        <div class="form-group">
          <label>Gender</label>
          <select id="pGender">
            <option value="">Select Gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>
        </div>
        <div class="form-group">
          <label>Designation</label>
          <input type="text" id="pDesignation">
        </div>
        <div class="form-group">
          <label>Phone Number</label>
          <input type="text" id="pPhone">
        </div>
        <div class="form-group">
          <label>Region/Division</label>
          <input type="text" id="pRegion">
        </div>
        <div class="form-group">
          <label>Category</label>
          <select id="pCategory">
            <option value="">Auto-detect</option>
            <option value="Men">Men</option>
            <option value="Women">Women</option>
            <option value="Stakeholders">Stakeholders</option>
          </select>
        </div>
        <div class="form-group full-width">
          <label>Remarks</label>
          <textarea id="pRemarks" rows="2"></textarea>
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
      <h3>Delete Person</h3>
      <button class="modal-close" onclick="closeDeleteModal()">&times;</button>
    </div>
    <p id="deleteMsg" style="padding:1rem">Are you sure you want to delete this person?</p>
    <div class="modal-actions">
      <button type="button" class="btn btn-secondary" onclick="closeDeleteModal()">Cancel</button>
      <button type="button" class="btn btn-danger" id="confirmDeleteBtn" onclick="confirmDelete()">Delete</button>
    </div>
  </div>
</div>

<script>
let deleteId = null;
function showAddModal() {{
  document.getElementById('modalTitle').textContent = 'Add Person';
  document.getElementById('personId').value = '';
  document.getElementById('personForm').reset();
  document.getElementById('personModal').classList.add('open');
}}
function editPerson(id, name, gender, designation, phone, region, category, remarks) {{
  document.getElementById('modalTitle').textContent = 'Edit Person';
  document.getElementById('personId').value = id;
  document.getElementById('pName').value = name;
  document.getElementById('pGender').value = gender;
  document.getElementById('pDesignation').value = designation;
  document.getElementById('pPhone').value = phone;
  document.getElementById('pRegion').value = region;
  document.getElementById('pCategory').value = category;
  document.getElementById('pRemarks').value = remarks;
  document.getElementById('personModal').classList.add('open');
}}
function closeModal() {{ document.getElementById('personModal').classList.remove('open'); }}
function closeDeleteModal() {{ document.getElementById('deleteModal').classList.remove('open'); deleteId = null; }}
function savePerson(e) {{
  e.preventDefault();
  const id = document.getElementById('personId').value;
  const data = new FormData();
  data.append('name', document.getElementById('pName').value);
  data.append('gender', document.getElementById('pGender').value);
  data.append('designation', document.getElementById('pDesignation').value);
  data.append('phone_number', document.getElementById('pPhone').value);
  data.append('region_division', document.getElementById('pRegion').value);
  data.append('category', document.getElementById('pCategory').value);
  data.append('remarks', document.getElementById('pRemarks').value);
  const method = id ? 'PUT' : 'POST';
  const url = id ? `/api/people/${{id}}` : '/api/people';
  const btn = document.getElementById('saveBtn');
  btn.disabled = true; btn.textContent = 'Saving...';
  fetch(url, {{ method, body: data }})
    .then(r => r.json())
    .then(d => {{ if(d.success) {{ closeModal(); location.reload(); }} else {{ alert('Error: '+d.error); }} }})
    .catch(e => alert('Error: '+e))
    .finally(() => {{ btn.disabled = false; btn.textContent = 'Save'; }});
}}
function deletePerson(id, name) {{
  deleteId = id;
  document.getElementById('deleteMsg').textContent = `Are you sure you want to delete "${{name}}"?`;
  document.getElementById('deleteModal').classList.add('open');
}}
function confirmDelete() {{
  if(!deleteId) return;
  const btn = document.getElementById('confirmDeleteBtn');
  btn.disabled = true; btn.textContent = 'Deleting...';
  fetch(`/api/people/${{deleteId}}`, {{ method: 'DELETE' }})
    .then(r => r.json())
    .then(d => {{ if(d.success) {{ closeDeleteModal(); location.reload(); }} else {{ alert('Error: '+d.error); }} }})
    .catch(e => alert('Error: '+e))
    .finally(() => {{ btn.disabled = false; btn.textContent = 'Delete'; deleteId = null; }});
}}
function searchPeople() {{
  const q = document.getElementById('searchInput').value;
  const params = new URLSearchParams(window.location.search);
  params.set('search', q);
  params.delete('page');
  window.location.href = '/people?' + params.toString();
}}
</script>
</body>
</html>"""
