from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import cast, Date
from datetime import date
from app.database import get_db
from app.authentication.auth import get_current_user
from app.models.attendance import Attendance
from app.services.dashboard_service import (
    get_category_distribution, get_gender_distribution,
    get_weekly_trend, get_dashboard_stats, get_designation_analytics,
    get_verified_breakdown, get_statistics_summary,
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


@router.get("/api/analytics/designations")
async def designations_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_designation_analytics(db)


@router.get("/api/analytics/verified-breakdown")
async def verified_breakdown_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_verified_breakdown(db)


@router.get("/api/analytics/statistics")
async def statistics_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_statistics_summary(db)


@router.get("/api/analytics/verified-persons")
async def verified_persons_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    from datetime import timedelta
    today = date.today()
    yesterday = today - timedelta(days=1)

    def _fetch(d):
        rows = db.query(Attendance).filter(
            cast(Attendance.verification_date, Date) == d,
            Attendance.status == "Verified",
        ).order_by(Attendance.verification_time.desc()).all()
        return [
            {
                "id": r.id,
                "person_name": r.person_name,
                "gender": r.gender or "",
                "designation": r.designation or "",
                "category": r.category or "",
                "verification_time": r.verification_time.strftime("%Y-%m-%d %H:%M:%S") if r.verification_time else "",
                "verified_by_name": r.verified_by_name or "",
                "remarks": r.remarks or "",
            }
            for r in rows
        ]

    return {
        "today": _fetch(today),
        "yesterday": _fetch(yesterday),
    }


def _analytics_html(user):
    name = user.get("username", "User")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Analytics | DCLM Attendance</title>
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
        <div class="stat-card stat-blue"><div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg></div><div class="stat-info"><h3>...</h3><p>Total People</p></div></div>
        <div class="stat-card stat-green"><div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></div><div class="stat-info"><h3>...</h3><p>Verified Today</p></div></div>
        <div class="stat-card stat-purple"><div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg></div><div class="stat-info"><h3>...</h3><p>This Week</p></div></div>
        <div class="stat-card stat-cyan"><div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"/></svg></div><div class="stat-info"><h3 id="desigCount">...</h3><p>Designations</p></div></div>
      </div>

      <div class="vb-section" id="verifiedBreakdownSection">
        <h3 class="vb-title">Verified Attendance Overview</h3>
        <div class="vb-grid">

          <div class="vb-card vb-card--yesterday">
            <div class="vb-card-header">
              <span class="vb-label">Yesterday</span>
              <span class="vb-total vb-total--amber" id="vbYestTotal">--</span>
            </div>
            <div class="vb-progress-track">
              <div class="vb-progress-fill" id="vbYestBar" style="width:0%;background:#f59e0b"></div>
            </div>
            <div class="vb-gender-row">
              <div class="vb-gender-pill">
                <span class="vb-dot" style="background:#3b82f6"></span>
                <span class="vb-gender-num" id="vbYestMen">--</span>
                <span class="vb-gender-label">Men</span>
                <span class="vb-gender-rate" id="vbYestMenRate">--</span>
              </div>
              <div class="vb-gender-pill">
                <span class="vb-dot" style="background:#ec4899"></span>
                <span class="vb-gender-num" id="vbYestWomen">--</span>
                <span class="vb-gender-label">Women</span>
                <span class="vb-gender-rate" id="vbYestWomenRate">--</span>
              </div>
            </div>
            <div class="vb-detail" id="vbYestDetail"></div>
          </div>

          <div class="vb-card vb-card--today">
            <div class="vb-card-header">
              <span class="vb-label">Today</span>
              <span class="vb-total vb-total--green" id="vbTodayTotal">--</span>
            </div>
            <div class="vb-progress-track">
              <div class="vb-progress-fill" id="vbTodayBar" style="width:0%;background:#10b981"></div>
            </div>
            <div class="vb-gender-row">
              <div class="vb-gender-pill">
                <span class="vb-dot" style="background:#3b82f6"></span>
                <span class="vb-gender-num" id="vbTodayMen">--</span>
                <span class="vb-gender-label">Men</span>
                <span class="vb-gender-rate" id="vbTodayMenRate">--</span>
              </div>
              <div class="vb-gender-pill">
                <span class="vb-dot" style="background:#ec4899"></span>
                <span class="vb-gender-num" id="vbTodayWomen">--</span>
                <span class="vb-gender-label">Women</span>
                <span class="vb-gender-rate" id="vbTodayWomenRate">--</span>
              </div>
            </div>
            <div class="vb-detail" id="vbTodayDetail"></div>
          </div>

          <div class="vb-card vb-card--alltime">
            <div class="vb-card-header">
              <span class="vb-label">All Time</span>
              <span class="vb-total vb-total--purple" id="vbAllTotal">--</span>
            </div>
            <div class="vb-progress-track">
              <div class="vb-progress-fill" id="vbAllBar" style="width:0%;background:#8b5cf6"></div>
            </div>
            <div class="vb-gender-row">
              <div class="vb-gender-pill">
                <span class="vb-dot" style="background:#3b82f6"></span>
                <span class="vb-gender-num" id="vbAllMen">--</span>
                <span class="vb-gender-label">Men</span>
              </div>
              <div class="vb-gender-pill">
                <span class="vb-dot" style="background:#ec4899"></span>
                <span class="vb-gender-num" id="vbAllWomen">--</span>
                <span class="vb-gender-label">Women</span>
              </div>
            </div>
            <div class="vb-detail" id="vbAllDetail"></div>
          </div>

        </div>
      </div>

        <div class="charts-grid">
          <div class="card"><div class="card-header"><h3>Verified by Gender (Today)</h3></div><div class="card-body donut-container"><canvas id="genderChart"></canvas></div></div>
          <div class="card"><div class="card-header"><h3>Verified by Category (Today)</h3></div><div class="card-body donut-container"><canvas id="categoryChart"></canvas></div></div>
        </div>

      <div id="statsSummarySection" class="stat-card" style="padding:20px;margin:16px 0">
        <h3 style="margin:0 0 16px 0;font-size:16px">Statistical Summary</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px">
          <div style="padding:12px;background:var(--bg-secondary);border-radius:8px;text-align:center">
            <div style="font-size:24px;font-weight:700;color:#3b82f6" id="statAvg">--</div>
            <div style="font-size:11px;color:var(--text-secondary)">Avg Attendance Rate</div>
          </div>
          <div style="padding:12px;background:var(--bg-secondary);border-radius:8px;text-align:center">
            <div style="font-size:24px;font-weight:700;color:#10b981" id="statMedian">--</div>
            <div style="font-size:11px;color:var(--text-secondary)">Median Rate</div>
          </div>
          <div style="padding:12px;background:var(--bg-secondary);border-radius:8px;text-align:center">
            <div style="font-size:24px;font-weight:700;color:#f59e0b" id="statStd">--</div>
            <div style="font-size:11px;color:var(--text-secondary)">Std Deviation</div>
          </div>
          <div style="padding:12px;background:var(--bg-secondary);border-radius:8px;text-align:center">
            <div style="font-size:24px;font-weight:700;color:#8b5cf6" id="statAbove80">--</div>
            <div style="font-size:11px;color:var(--text-secondary)">Above 80% Rate</div>
          </div>
          <div style="padding:12px;background:var(--bg-secondary);border-radius:8px;text-align:center">
            <div style="font-size:24px;font-weight:700;color:#ef4444" id="statBelow50">--</div>
            <div style="font-size:11px;color:var(--text-secondary)">Below 50% Rate</div>
          </div>
          <div style="padding:12px;background:var(--bg-secondary);border-radius:8px;text-align:center">
            <div style="font-size:24px;font-weight:700;color:#06b6d4" id="statDailyAvg">--</div>
            <div style="font-size:11px;color:var(--text-secondary)">Daily Avg Verified</div>
          </div>
        </div>
      </div>

      <div class="charts-grid" style="margin-top:16px">
        <div class="card full-width"><div class="card-header"><h3>Weekly Attendance Trend</h3></div><div class="card-body"><canvas id="weeklyChart"></canvas></div></div>
      </div>

      <div class="card" style="margin-top:16px">
        <div class="card-header" style="flex-direction:column;align-items:stretch">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
            <h3 style="margin:0">Verified Persons</h3>
            <div style="display:flex;gap:8px;align-items:center">
              <input type="text" id="vpSearch" class="desig-search" placeholder="Search..." onkeyup="filterVpTable(this.value)">
              <button class="btn btn-sm" style="background:var(--primary);color:#fff;border:none;border-radius:6px;padding:6px 14px;cursor:pointer;font-size:12px;font-weight:600" onclick="downloadCsv()">Download CSV</button>
            </div>
          </div>
          <div class="tabs" style="margin-top:8px">
            <button class="tab-btn active" onclick="switchVpTab('today',this)" id="vpTabToday">Today</button>
            <button class="tab-btn" onclick="switchVpTab('yesterday',this)" id="vpTabYest">Yesterday</button>
          </div>
        </div>
        <div class="table-wrapper">
          <table class="data-table" id="vpTable">
            <thead>
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Gender</th>
                <th>Designation</th>
                <th>Category</th>
                <th>Time</th>
                <th>Verified By</th>
                <th>Remarks</th>
              </tr>
            </thead>
            <tbody id="vpTableBody"><tr><td colspan="8" class="empty-row">Loading...</td></tr></tbody>
          </table>
        </div>
        <div style="padding:8px 16px;font-size:11px;color:var(--text-muted);border-top:1px solid var(--border)">
          <span id="vpCount"></span>
        </div>
      </div>

      <div class="designation-section" id="designationSection">
        <div class="designation-header">
          <h3>Designation Matrix</h3>
          <p class="text-muted">Comprehensive breakdown by role and designation</p>
        </div>

        <div class="charts-grid">
          <div class="card"><div class="card-header"><h3>People by Designation</h3></div><div class="card-body"><canvas id="desigBarChart"></canvas></div></div>
          <div class="card"><div class="card-header"><h3>Gender Split by Designation</h3></div><div class="card-body"><canvas id="desigGenderChart"></canvas></div></div>
        </div>

        <div class="designation-kpi-grid" id="desigKpis"></div>

        <div class="card" style="margin-top:16px">
          <div class="card-header">
            <h3>Designation Detail</h3>
            <input type="text" id="desigSearch" class="desig-search" placeholder="Filter designations..." onkeyup="filterDesigTable(this.value)">
          </div>
          <div class="table-wrapper">
            <table class="data-table designation-table">
              <thead>
                <tr>
                  <th>Designation</th>
                  <th>Count</th>
                  <th>% Share</th>
                  <th>Male</th>
                  <th>Female</th>
                  <th>Verified Today</th>
                  <th>This Week</th>
                  <th>Attendance Rate</th>
                </tr>
              </thead>
              <tbody id="desigTableBody"><tr><td colspan="8" class="empty-row">Loading...</td></tr></tbody>
            </table>
          </div>
        </div>
      </div>

    </div>
  </main>
</div>
<script>
async function loadData() {{
  try {{
    const overview = await fetch('/api/analytics/overview').then(r => r.json());
    document.getElementById('overviewStats').innerHTML = `
      <div class="stat-card stat-blue"><div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg></div><div class="stat-info"><h3>${{overview.total_persons}}</h3><p>Total People</p></div></div>
      <div class="stat-card stat-green"><div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></div><div class="stat-info"><h3>${{overview.today_verified}}</h3><p>Verified Today</p></div></div>
      <div class="stat-card stat-purple"><div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg></div><div class="stat-info"><h3>${{overview.weekly_count}} <small style="font-size:12px;color:var(--text-secondary)">${{overview.weekly_percent}}%</small></h3><p>This Week</p></div></div>
      <div class="stat-card stat-cyan"><div class="stat-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"/></svg></div><div class="stat-info"><h3 id="desigCount">...</h3><p>Designations</p></div></div>
    `;
  }} catch(e) {{ console.error('overview', e); }}

  try {{
    const vb = await fetch('/api/analytics/verified-breakdown').then(r => r.json());
    const y = vb.yesterday;
    const t = vb.today;
    const a = vb.alltime;

    document.getElementById('vbYestTotal').textContent = y.total;
    document.getElementById('vbYestMen').textContent = y.men;
    document.getElementById('vbYestWomen').textContent = y.women;
    document.getElementById('vbYestMenRate').textContent = y.men_rate + '%';
    document.getElementById('vbYestWomenRate').textContent = y.women_rate + '%';
    document.getElementById('vbYestDetail').textContent = y.rate + '% attendance rate out of ' + vb.total_active + ' active people';
    document.getElementById('vbYestBar').style.width = Math.min(y.rate, 100) + '%';

    document.getElementById('vbTodayTotal').textContent = t.total;
    document.getElementById('vbTodayMen').textContent = t.men;
    document.getElementById('vbTodayWomen').textContent = t.women;
    document.getElementById('vbTodayMenRate').textContent = t.men_rate + '%';
    document.getElementById('vbTodayWomenRate').textContent = t.women_rate + '%';
    document.getElementById('vbTodayDetail').textContent = t.rate + '% attendance rate out of ' + vb.total_active + ' active people';
    document.getElementById('vbTodayBar').style.width = Math.min(t.rate, 100) + '%';

    document.getElementById('vbAllTotal').textContent = a.total;
    document.getElementById('vbAllMen').textContent = a.men;
    document.getElementById('vbAllWomen').textContent = a.women;
    document.getElementById('vbAllDetail').textContent = a.total + ' total verifications recorded';
    document.getElementById('vbAllBar').style.width = Math.min(a.rate, 100) + '%';

    const gCtx = document.getElementById('genderChart').getContext('2d');
    const gLabels = Object.keys(t.by_gender);
    const gValues = Object.values(t.by_gender);
    const gColors = gLabels.map(l => l === 'Male' ? '#3b82f6' : l === 'Female' ? '#ec4899' : '#94a3b8');
    new Chart(gCtx, {{
      type: 'doughnut',
      data: {{ labels: gLabels, datasets: [{{ data: gValues, backgroundColor: gColors, borderWidth: 2, borderColor: '#fff' }}] }},
      options: {{ responsive: true, maintainAspectRatio: true, plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 12, font: {{ size: 12 }} }} }} }} }}
    }});

    const cCtx = document.getElementById('categoryChart').getContext('2d');
    const cLabels = Object.keys(t.by_category);
    const cValues = Object.values(t.by_category);
    const cColors = ['#3b82f6','#ec4899','#f59e0b','#10b981'];
    new Chart(cCtx, {{
      type: 'pie',
      data: {{ labels: cLabels, datasets: [{{ data: cValues, backgroundColor: cColors.slice(0, cLabels.length), borderWidth: 2, borderColor: '#fff' }}] }},
      options: {{ responsive: true, maintainAspectRatio: true, plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 12, font: {{ size: 12 }} }} }} }} }}
    }});
  }} catch(e) {{ console.error('verified breakdown', e); }}

  try {{
    const st = await fetch('/api/analytics/statistics').then(r => r.json());
    document.getElementById('statAvg').textContent = st.avg_attendance_rate + '%';
    document.getElementById('statMedian').textContent = st.median_attendance_rate + '%';
    document.getElementById('statStd').textContent = st.std_attendance_rate + '%';
    document.getElementById('statAbove80').textContent = st.designations_above_80 + ' / ' + st.total_designations;
    document.getElementById('statBelow50').textContent = st.designations_below_50 + ' / ' + st.total_designations;
    document.getElementById('statDailyAvg').textContent = st.daily_average;
  }} catch(e) {{ console.error('statistics', e); }}

  try {{
    const trendData = await fetch('/api/analytics/weekly-trend').then(r => r.json());
    const ctx = document.getElementById('weeklyChart').getContext('2d');
    new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: trendData.map(d => d.date),
        datasets: [{{ label: 'Attendance', data: trendData.map(d => d.count), borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)', fill: true, tension: 0.3, borderWidth: 2, pointRadius: 4 }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: true, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }} }}
    }});
  }} catch(e) {{ console.error('weekly trend', e); }}

  try {{
    const vpRes = await fetch('/api/analytics/verified-persons').then(r => r.json());
    window._vpToday = vpRes.today || [];
    window._vpYest = vpRes.yesterday || [];
    window._vpActiveTab = 'today';
    renderVpTable(window._vpToday);
  }} catch(e) {{ console.error('verified persons', e); }}

  try {{
    const desigData = await fetch('/api/analytics/designations').then(r => r.json());
    const d = desigData.designations || [];
    const dc = document.getElementById('desigCount');
    if (dc) dc.textContent = desigData.total_designations;

    const palette = ['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ec4899','#06b6d4','#f97316','#14b8a6','#6366f1','#84cc16'];

    if (d.length > 0) {{
      new Chart(document.getElementById('desigBarChart').getContext('2d'), {{
        type: 'bar',
        data: {{
          labels: d.map(x => x.designation),
          datasets: [{{ label: 'Count', data: d.map(x => x.total), backgroundColor: palette.slice(0, d.length), borderWidth: 0, borderRadius: 6 }}]
        }},
        options: {{
          responsive: true, maintainAspectRatio: true,
          indexAxis: d.length > 6 ? 'y' : 'x',
          plugins: {{ legend: {{ display: false }} }},
          scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }}, x: {{ ticks: {{ maxRotation: 45 }} }} }}
        }}
      }});

      new Chart(document.getElementById('desigGenderChart').getContext('2d'), {{
        type: 'bar',
        data: {{
          labels: desigData.gender_chart.map(x => x.designation),
          datasets: [
            {{ label: 'Male', data: desigData.gender_chart.map(x => x.male), backgroundColor: '#3b82f6', borderRadius: 4 }},
            {{ label: 'Female', data: desigData.gender_chart.map(x => x.female), backgroundColor: '#ec4899', borderRadius: 4 }},
            {{ label: 'Other', data: desigData.gender_chart.map(x => x.other), backgroundColor: '#94a3b8', borderRadius: 4 }},
          ]
        }},
        options: {{
          responsive: true, maintainAspectRatio: true,
          plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 10, font: {{ size: 11 }} }} }} }},
          scales: {{ x: {{ stacked: true, ticks: {{ maxRotation: 45 }} }}, y: {{ stacked: true, beginAtZero: true, ticks: {{ stepSize: 1 }} }} }}
        }}
      }});
    }}

    let kpiHtml = '';
    d.forEach((desig, i) => {{
      const color = palette[i % palette.length];
      const male = desig.gender['Male'] || 0;
      const female = desig.gender['Female'] || 0;
      const total = male + female;
      const malePct = total > 0 ? Math.round(male / total * 100) : 0;
      const femalePct = total > 0 ? 100 - malePct : 0;
      const rateColor = desig.attendance_rate >= 80 ? '#10b981' : desig.attendance_rate >= 50 ? '#f59e0b' : '#ef4444';
      kpiHtml += `
        <div class="desig-kpi-card">
          <div class="desig-kpi-accent" style="background:${{color}}"></div>
          <div class="desig-kpi-body">
            <h4>${{desig.designation}}</h4>
            <div class="desig-kpi-stats">
              <div class="desig-kpi-num">${{desig.total}}</div>
              <div class="desig-kpi-pct">${{desig.percentage}}% of total</div>
            </div>
            <div class="desig-kpi-bar-track">
              <div class="desig-kpi-bar-fill" style="width:${{malePct}}%;background:#3b82f6"></div>
              <div class="desig-kpi-bar-fill" style="width:${{femalePct}}%;background:#ec4899"></div>
            </div>
            <div class="desig-kpi-bar-labels"><span>M ${{male}}</span><span>F ${{female}}</span></div>
            <div class="desig-kpi-rate">
              <span class="desig-kpi-rate-dot" style="background:${{rateColor}}"></span>
              ${{desig.attendance_rate}}% today
            </div>
          </div>
        </div>`;
    }});
    document.getElementById('desigKpis').innerHTML = kpiHtml;

    let tableHtml = '';
    d.forEach((desig, i) => {{
      const color = palette[i % palette.length];
      const rateColor = desig.attendance_rate >= 80 ? '#10b981' : desig.attendance_rate >= 50 ? '#f59e0b' : '#ef4444';
      const rateBg = desig.attendance_rate >= 80 ? 'rgba(16,185,129,0.1)' : desig.attendance_rate >= 50 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)';
      tableHtml += `
        <tr class="desig-row" data-name="${{desig.designation.toLowerCase()}}">
          <td><span class="desig-dot" style="background:${{color}}"></span> ${{desig.designation}}</td>
          <td><strong>${{desig.total}}</strong></td>
          <td>${{desig.percentage}}%</td>
          <td>${{desig.gender['Male'] || 0}}</td>
          <td>${{desig.gender['Female'] || 0}}</td>
          <td>${{desig.verified_today}}</td>
          <td>${{desig.verified_week}}</td>
          <td><span class="desig-rate-badge" style="color:${{rateColor}};background:${{rateBg}}">${{desig.attendance_rate}}%</span></td>
        </tr>`;
    }});
    document.getElementById('desigTableBody').innerHTML = tableHtml || '<tr><td colspan="8" class="empty-row">No designation data</td></tr>';
  }} catch(e) {{ console.error('designation analytics', e); }}
}}
loadData();
function filterDesigTable(val) {{
  const rows = document.querySelectorAll('.desig-row');
  const q = val.toLowerCase();
  rows.forEach(r => {{ r.style.display = r.dataset.name.includes(q) ? '' : 'none'; }});
}}

function renderVpTable(data) {{
  const countEl = document.getElementById('vpCount');
  countEl.textContent = data.length + ' person(s) verified';
  if (!data || data.length === 0) {{
    document.getElementById('vpTableBody').innerHTML = '<tr><td colspan="8" class="empty-row">No verified persons</td></tr>';
    return;
  }}
  let html = '';
  data.forEach((p, i) => {{
    const time = p.verification_time.split(' ')[1] || p.verification_time;
    html += `<tr class="vp-row" data-search="${{(p.person_name+' '+p.designation+' '+p.category+' '+p.gender).toLowerCase()}}">
      <td>${{i+1}}</td>
      <td>${{p.person_name}}</td>
      <td>${{p.gender}}</td>
      <td>${{p.designation}}</td>
      <td>${{p.category}}</td>
      <td>${{time}}</td>
      <td>${{p.verified_by_name}}</td>
      <td>${{p.remarks || '-'}}</td>
    </tr>`;
  }});
  document.getElementById('vpTableBody').innerHTML = html;
}}

function switchVpTab(tab, btn) {{
  window._vpActiveTab = tab;
  document.querySelectorAll('#vpTabToday,#vpTabYest').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('vpSearch').value = '';
  const data = tab === 'today' ? window._vpToday : window._vpYest;
  renderVpTable(data);
}}

function filterVpTable(val) {{
  const rows = document.querySelectorAll('.vp-row');
  const q = val.toLowerCase();
  rows.forEach(r => {{ r.style.display = r.dataset.search.includes(q) ? '' : 'none'; }});
}}

function downloadCsv() {{
  const data = window._vpActiveTab === 'today' ? window._vpToday : window._vpYest;
  const label = window._vpActiveTab === 'today' ? 'Today' : 'Yesterday';
  if (!data || !data.length) {{ alert('No data to download'); return; }}
  const headers = ['#','Name','Gender','Designation','Category','Time','Verified By','Remarks'];
  const rows = data.map((p,i) => [
    i+1, p.person_name, p.gender, p.designation, p.category,
    p.verification_time, p.verified_by_name, p.remarks || ''
  ]);
  let csv = headers.join(',') + '\\n';
  rows.forEach(r => {{
    csv += r.map(v => '"' + String(v).replace(/"/g, '""') + '"').join(',') + '\\n';
  }});
  const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'verified_' + label.toLowerCase() + '_' + new Date().toISOString().slice(0,10) + '.csv';
  a.click();
  URL.revokeObjectURL(url);
}}
</script>
</body>
</html>"""
