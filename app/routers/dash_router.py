from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.authentication.auth import get_current_user
from app.services.dashboard_service import (
    get_dashboard_stats, get_weekly_trend,
    get_category_distribution, get_gender_distribution,
    get_todays_attendance_by_category,
)
from app.routers.people import _sidebar_html

router = APIRouter(prefix="", tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    stats = get_dashboard_stats(db)
    return HTMLResponse(_dashboard_html(user, stats))


@router.get("/api/dashboard/stats")
async def dashboard_stats_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    stats = get_dashboard_stats(db)
    return stats


@router.get("/api/dashboard/weekly-trend")
async def weekly_trend_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_weekly_trend(db)


@router.get("/api/dashboard/category-distribution")
async def category_dist_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_category_distribution(db)


@router.get("/api/dashboard/todays-attendance")
async def todays_att_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_todays_attendance_by_category(db)


def _dashboard_html(user, stats):
    name = user.get("username", "User")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard | Attendance Verification</title>
<link rel="stylesheet" href="/static/css/dashboard.css">
<link rel="stylesheet" href="/static/css/style.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
</head>
<body>
<div class="app-container">
  {_sidebar_html(user, 'dashboard')}
  <main class="main-content">
    <header class="topbar">
      <div class="topbar-left">
        <button class="hamburger-btn" id="hamburgerBtn" onclick="toggleSidebar()">
          <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
        </button>
        <h2>Dashboard</h2>
      </div>
      <div class="topbar-right">
        <div class="user-badge"><span class="user-avatar">{name[0].upper()}</span><span class="user-name">{name}</span></div>
      </div>
    </header>
    <div class="content-area">
      <div class="stats-grid">
        <div class="stat-card stat-blue">
          <div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg></div>
          <div class="stat-info"><h3>{stats["total_persons"]}</h3><p>Total People</p></div>
        </div>
        <div class="stat-card stat-green">
          <div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></div>
          <div class="stat-info"><h3>{stats["today_verified"]}</h3><p>Verified Today</p></div>
        </div>
        <div class="stat-card stat-red">
          <div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg></div>
          <div class="stat-info"><h3>{stats["not_verified"]}</h3><p>Not Verified</p></div>
        </div>
        <div class="stat-card stat-purple">
          <div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg></div>
          <div class="stat-info"><h3>{stats["weekly_count"]}</h3><p>This Week ({stats["weekly_percent"]}%)</p></div>
        </div>
      </div>
      <p style="font-size:11px;color:var(--text-secondary);font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;margin-top:-12px">By Category</p>
      <div class="stats-grid secondary">
        <div class="stat-card stat-cyan">
          <div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></div>
          <div class="stat-info"><h3>{stats["men_count"]}</h3><p>Men</p></div>
        </div>
        <div class="stat-card stat-pink">
          <div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></div>
          <div class="stat-info"><h3>{stats["women_count"]}</h3><p>Women</p></div>
        </div>
        <div class="stat-card stat-orange">
          <div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg></div>
          <div class="stat-info"><h3>{stats["stakeholder_count"]}</h3><p>Stakeholders</p></div>
        </div>
      </div>
      <div class="charts-grid">
        <div class="card"><div class="card-header"><h3>Weekly Attendance Trend</h3></div><div class="card-body"><canvas id="weeklyChart"></canvas></div></div>
        <div class="card"><div class="card-header"><h3>Category Distribution</h3></div><div class="card-body"><canvas id="categoryChart"></canvas></div></div>
        <div class="card"><div class="card-header"><h3>Today's Attendance by Category</h3></div><div class="card-body"><canvas id="todayChart"></canvas></div></div>
      </div>
    </div>
  </main>
</div>
<script>
async function loadChart(url, canvasId, type, labelKey, valueKey, colors) {{
  try {{
    const res = await fetch(url);
    const data = await res.json();
    const ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {{
      type: type,
      data: {{
        labels: data.map(d => d[labelKey]),
        datasets: [{{
          label: 'Count',
          data: data.map(d => d[valueKey]),
          backgroundColor: colors || ['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ec4899'],
          borderColor: '#fff',
          borderWidth: 2,
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }},
      }}
    }});
  }} catch(e) {{ console.error(canvasId, e); }}
}}
loadChart('/api/dashboard/weekly-trend', 'weeklyChart', 'line', 'date', 'count', ['#3b82f6']);
loadChart('/api/dashboard/category-distribution', 'categoryChart', 'doughnut', 'category', 'count', ['#3b82f6','#ec4899','#f59e0b']);
loadChart('/api/dashboard/todays-attendance', 'todayChart', 'bar', 'category', 'count', ['#10b981','#8b5cf6','#06b6d4']);
</script>
</body>
</html>"""
