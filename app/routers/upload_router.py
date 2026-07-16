import os
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.authentication.auth import get_current_user
from app.services.upload_service import parse_upload_file, import_records
from app.services.audit_service import create_log
from app.config import settings
from app.utilities.helpers import allowed_file, save_upload_file, get_client_ip
from app.routers.people import _sidebar_html

router = APIRouter(prefix="", tags=["upload"])


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return HTMLResponse(_upload_html(user))


@router.post("/api/upload/preview")
async def preview_upload(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not allowed_file(file.filename or ""):
        raise HTTPException(status_code=400, detail="Invalid file format. Use .xlsx, .xls, or .csv")
    filepath = save_upload_file(file, settings.UPLOAD_FOLDER)
    if not filepath:
        raise HTTPException(status_code=400, detail="Could not save file")
    try:
        records = parse_upload_file(filepath)
        preview = records[:20]
        return {
            "total_records": len(records),
            "preview": [
                {
                    "name": r.get("name", ""),
                    "gender": r.get("gender", ""),
                    "designation": r.get("designation", ""),
                    "phone_number": r.get("phone_number", ""),
                    "region_division": r.get("region_division", ""),
                    "category": r.get("category", ""),
                }
                for r in preview
            ],
            "filepath": filepath,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/upload/import")
async def import_uploaded(
    request: Request,
    filepath: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="File not found")
    try:
        records = parse_upload_file(filepath)
        result = import_records(db, records)
        create_log(
            db, user.get("user_id"), "upload", "Person", None,
            f"Uploaded file: imported {result['imported']}, skipped {result['skipped']}",
            get_client_ip(request),
        )
        os.remove(filepath)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _upload_html(user):
    name = user.get("username", "User")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Upload Data | Attendance Verification</title>
<link rel="stylesheet" href="/static/css/dashboard.css">
<link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
<div class="app-container">
  {_sidebar_html(user, 'upload')}
  <main class="main-content">
    <header class="topbar">
      <div class="topbar-left">
        <button class="hamburger-btn" id="hamburgerBtn" onclick="toggleSidebar()">
          <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
        </button>
        <h2>Upload Data</h2>
      </div>
      <div class="topbar-right">
        <div class="user-badge"><span class="user-avatar">{name[0].upper()}</span><span class="user-name">{name}</span></div>
      </div>
    </header>
    <div class="content-area">
      <div class="card">
        <div class="card-header"><h3>Import People from Excel / CSV</h3></div>
        <div class="card-body">
          <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
            <svg viewBox="0 0 24 24" width="48" height="48"><path fill="currentColor" d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z"/></svg>
            <p>Drag & drop your file here or click to browse</p>
            <span class="text-muted">Supports: .xlsx, .xls, .csv</span>
            <input type="file" id="fileInput" accept=".xlsx,.xls,.csv" hidden onchange="handleFile(this)">
          </div>
          <div id="uploadStatus" class="upload-status" style="display:none"></div>
          <div id="previewSection" style="display:none">
            <div class="card-header"><h3>Preview</h3>
              <div>
                <span id="totalCount" class="badge badge-info"></span>
                <button class="btn btn-primary" id="importBtn" onclick="importData()">Import All</button>
              </div>
            </div>
            <div class="table-wrapper"><table class="data-table"><thead><tr><th>Name</th><th>Gender</th><th>Designation</th><th>Phone</th><th>Region</th><th>Category</th></tr></thead><tbody id="previewBody"></tbody></table></div>
          </div>
          <div id="debugPanel" style="display:none;margin-top:16px">
            <div class="card-header"><h3>Raw API Response (Debug)</h3></div>
            <pre id="debugJson" style="background:#f5f5f5;padding:16px;border-radius:8px;font-size:12px;overflow:auto;max-height:300px;white-space:pre-wrap"></pre>
          </div>
        </div>
      </div>
    </div>
  </main>
</div>
<script>
let uploadedFilepath = '';
function handleFile(input) {{
  const file = input.files[0];
  if(!file) return;
  const status = document.getElementById('uploadStatus');
  status.style.display = 'block';
  status.className = 'upload-status info';
  status.innerHTML = 'Analyzing file...';
  const fd = new FormData();
  fd.append('file', file);
  fetch('/api/upload/preview', {{ method: 'POST', body: fd }})
    .then(r => r.json())
    .then(d => {{
      if(d.total_records === undefined) throw new Error('Invalid response');
      console.log('PREVIEW DATA:', JSON.stringify(d.preview, null, 2));
      d.preview.forEach(function(r, i) {{ console.log('Row ' + i + ' gender:', JSON.stringify(r.gender), 'type:', typeof r.gender); }});
      document.getElementById('debugJson').textContent = JSON.stringify(d.preview, null, 2);
      document.getElementById('debugPanel').style.display = 'block';
      uploadedFilepath = d.filepath;
      document.getElementById('previewSection').style.display = 'block';
      document.getElementById('totalCount').textContent = d.total_records + ' records found';
      const tbody = document.getElementById('previewBody');
      tbody.innerHTML = '';
      d.preview.forEach(r => {{
        tbody.innerHTML += `<tr><td>${{r.name}}</td><td>${{r.gender||''}}</td><td>${{r.designation||''}}</td><td>${{r.phone_number||''}}</td><td>${{r.region_division||''}}</td><td>${{r.category||''}}</td></tr>`;
      }});
      status.style.display = 'none';
    }})
    .catch(e => {{
      status.className = 'upload-status error';
      status.innerHTML = 'Error: ' + e.message;
    }});
}}
function importData() {{
  if(!uploadedFilepath) return;
  const btn = document.getElementById('importBtn');
  btn.disabled = true; btn.textContent = 'Importing...';
  const fd = new FormData();
  fd.append('filepath', uploadedFilepath);
  fetch('/api/upload/import', {{ method: 'POST', body: fd }})
    .then(r => r.json())
    .then(d => {{
      document.getElementById('uploadStatus').style.display = 'block';
      document.getElementById('uploadStatus').className = 'upload-status success';
      document.getElementById('uploadStatus').innerHTML = `Success! ${{d.imported}} imported, ${{d.skipped}} skipped. <a href="/people">View People</a>`;
      document.getElementById('previewSection').style.display = 'none';
      btn.textContent = 'Import All';
      btn.disabled = false;
    }})
    .catch(e => {{
      document.getElementById('uploadStatus').className = 'upload-status error';
      document.getElementById('uploadStatus').innerHTML = 'Error: ' + e.message;
      btn.textContent = 'Import All';
      btn.disabled = false;
    }});
}}
</script>
</body>
</html>"""
