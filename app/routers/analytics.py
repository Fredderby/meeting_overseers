from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.authentication.auth import get_current_user
from app.services.dashboard_service import (
    get_category_distribution, get_gender_distribution,
    get_weekly_trend, get_dashboard_stats,
)
from app.routers.people import _sidebar_html

router = APIRouter(prefix="", tags=["analytics"])


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return HTMLResponse(_analytics_html(user))


@router.get("/api/analytics/gender-distribution")
async def gender_dist_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_gender_distribution(db)


@router.get("/api/analytics/category-distribution")
async def category_dist_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_category_distribution(db)


@router.get("/api/analytics/weekly-trend")
async def weekly_trend_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_weekly_trend(db)


@router.get("/api/analytics/overview")
async def overview_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_dashboard_stats(db)


def _analytics_html(user):
    name = user.get("username", "User")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Analytics | Attendance Verification</title>
<link rel="stylesheet" href="/static/css/dashboard.css">
<link rel="stylesheet" href="/static/css/style.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
</head>
<body>
<div class="app-container">
  {_sidebar_html(user, 'analytics')}
  <main class="main-content">
    <header class="topbar">
      <div class="topbar-left">
        <button class="hamburger-btn" id="hamburgerBtn" onclick="toggleSidebar()">
          <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
        </button>
        <h2>Analytics</h2>
      </div>
      <div class="topbar-right">
        <div class="user-badge"><span class="user-avatar">{name[0].upper()}</span><span class="user-name">{name}</span></div>
      </div>
    </header>
    <div class="content-area">
      <div class="stats-grid" id="overviewStats">
        <div class="stat-card stat-blue"><h3>Loading...</h3><p>Total People</p></div>
        <div class="stat-card stat-green"><h3>...</h3><p>Verified Today</p></div>
        <div class="stat-card stat-purple"><h3>...</h3><p>This Week</p></div>
      </div>
      <div class="charts-grid">
        <div class="card"><div class="card-header"><h3>Gender Distribution</h3></div><div class="card-body"><canvas id="genderChart"></canvas></div></div>
        <div class="card"><div class="card-header"><h3>Category Distribution</h3></div><div class="card-body"><canvas id="categoryChart"></canvas></div></div>
        <div class="card full-width"><div class="card-header"><h3>Weekly Attendance Trend</h3></div><div class="card-body"><canvas id="weeklyChart"></canvas></div></div>
      </div>
    </div>
  </main>
</div>
<script>
async function loadData() {{
  try {{
    const overview = await fetch('/api/analytics/overview').then(r => r.json());
    document.getElementById('overviewStats').innerHTML = `
      <div class="stat-card stat-blue"><h3>${{overview.total_persons}}</h3><p>Total People</p></div>
      <div class="stat-card stat-green"><h3>${{overview.today_verified}}</h3><p>Verified Today</p></div>
      <div class="stat-card stat-purple"><h3>${{overview.weekly_count}} (${{overview.weekly_percent}}%)</h3><p>This Week</p></div>
    `;
  }} catch(e) {{}}

  async function makeChart(url, canvasId, type, labelKey, valueKey, label, colors) {{
    try {{
      const data = await fetch(url).then(r => r.json());
      const ctx = document.getElementById(canvasId).getContext('2d');
      new Chart(ctx, {{
        type: type,
        data: {{
          labels: data.map(d => d[labelKey]),
          datasets: [{{
            label: label,
            data: data.map(d => d[valueKey]),
            backgroundColor: colors || ['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ec4899','#06b6d4'],
            borderWidth: 2,
          }}]
        }},
        options: {{
          responsive: true,
          plugins: {{ legend: {{ position: 'bottom' }} }},
          scales: type !== 'pie' && type !== 'doughnut' ? {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }} : undefined,
        }}
      }});
    }} catch(e) {{ console.error(canvasId, e); }}
  }}
  makeChart('/api/analytics/gender-distribution', 'genderChart', 'doughnut', 'gender', 'count', 'Gender');
  makeChart('/api/analytics/category-distribution', 'categoryChart', 'pie', 'category', 'count', 'Category', ['#3b82f6','#ec4899','#f59e0b']);
  makeChart('/api/analytics/weekly-trend', 'weeklyChart', 'line', 'date', 'count', 'Attendance', ['#3b82f6']);
}}
loadData();
</script>
</body>
</html>"""
