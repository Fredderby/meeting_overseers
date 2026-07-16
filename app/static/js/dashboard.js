document.addEventListener('DOMContentLoaded', function() {
  loadStats();
  loadCharts();
  loadRecentVerifications();
  setupSidebar();
  setupGlobalSearch();
});

let categoryChart, trendChart, regionChart, pendingChart;

async function loadStats() {
  try {
    const res = await fetch('/api/dashboard/stats');
    const data = await res.json();
    renderStats(data);
  } catch (err) {
    console.error('Failed to load stats', err);
  }
}

function renderStats(data) {
  const container = document.getElementById('statsContainer');
  const cards = [
    { label: 'Total People', value: data.total_people, icon: 'people', color: '#667eea' },
    { label: 'Total Men', value: data.total_men, icon: 'person', color: '#3b82f6' },
    { label: 'Total Women', value: data.total_women, icon: 'person', color: '#ec4899' },
    { label: 'Stakeholders', value: data.total_stakeholders, icon: 'group', color: '#f59e0b' },
    { label: 'Verified Today', value: data.verified_today, icon: 'check', color: '#10b981' },
    { label: 'Pending', value: data.pending_verification, icon: 'clock', color: '#ef4444' },
  ];

  container.innerHTML = cards.map(c => `
    <div class="stat-card">
      <div class="stat-icon" style="background: ${c.color}20; color: ${c.color}">
        ${getIcon(c.icon)}
      </div>
      <div class="stat-value">${c.value.toLocaleString()}</div>
      <div class="stat-label">${c.label}</div>
    </div>
  `).join('');
}

function getIcon(type) {
  const icons = {
    people: '<svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>',
    person: '<svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>',
    group: '<svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>',
    check: '<svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>',
    clock: '<svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>',
  };
  return icons[type] || icons.people;
}

async function loadCharts() {
  try {
    const res = await fetch('/api/dashboard/charts');
    const data = await res.json();
    renderCategoryChart(data.category_breakdown);
    renderTrendChart(data.verification_trend);
    renderRegionChart(data.region_breakdown);
    renderPendingChart(data.pending_by_category);
  } catch (err) {
    console.error('Failed to load charts', err);
  }
}

function renderCategoryChart(data) {
  const ctx = document.getElementById('categoryChart').getContext('2d');
  if (categoryChart) categoryChart.destroy();

  categoryChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map(d => d.category),
      datasets: [{
        data: data.map(d => d.total),
        backgroundColor: ['#667eea', '#ec4899', '#f59e0b'],
        borderWidth: 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true } }
      },
      cutout: '65%',
    }
  });
}

function renderTrendChart(data) {
  const ctx = document.getElementById('trendChart').getContext('2d');
  if (trendChart) trendChart.destroy();

  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => {
        const parts = d.date.split('-');
        return parts[1] + '/' + parts[2];
      }),
      datasets: [{
        label: 'Verifications',
        data: data.map(d => d.count),
        borderColor: '#667eea',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointBackgroundColor: '#667eea',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { stepSize: 1 } },
        x: { grid: { display: false } }
      }
    }
  });
}

function renderRegionChart(data) {
  const ctx = document.getElementById('regionChart').getContext('2d');
  if (regionChart) regionChart.destroy();

  const sorted = [...data].sort((a, b) => b.total - a.total).slice(0, 10);

  regionChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sorted.map(d => d.region),
      datasets: [{
        label: 'Total',
        data: sorted.map(d => d.total),
        backgroundColor: '#667eea',
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { stepSize: 1 } },
        x: { grid: { display: false } }
      }
    }
  });
}

function renderPendingChart(data) {
  const ctx = document.getElementById('pendingChart').getContext('2d');
  if (pendingChart) pendingChart.destroy();

  pendingChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.category),
      datasets: [{
        label: 'Pending',
        data: data.map(d => d.count),
        backgroundColor: ['#667eea', '#ec4899', '#f59e0b'],
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        y: { grid: { display: false } },
        x: { beginAtZero: true, ticks: { stepSize: 1 } }
      }
    }
  });
}

async function loadRecentVerifications() {
  try {
    const res = await fetch('/api/attendance/logs?page=1&page_size=5');
    const data = await res.json();
    const tbody = document.getElementById('recentBody');
    tbody.innerHTML = data.logs.map(l => `
      <tr>
        <td>${l.person_name}</td>
        <td><span class="status-badge status-verified">${l.person_category}</span></td>
        <td>${formatTime(l.verification_time)}</td>
        <td>${l.verified_by_name || 'N/A'}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed to load recent verifications', err);
  }
}

function formatTime(iso) {
  if (!iso) return 'N/A';
  const d = new Date(iso);
  return d.toLocaleString();
}

function setupSidebar() {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');

  if (toggle && sidebar) {
    toggle.addEventListener('click', function() {
      sidebar.classList.toggle('open');
    });
  }
}

function setupGlobalSearch() {
  const searchInput = document.getElementById('globalSearch');
  if (!searchInput) return;

  let timeout;
  searchInput.addEventListener('input', function() {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      const q = this.value.trim();
      if (q.length >= 2) {
        window.location.href = `/attendance?q=${encodeURIComponent(q)}`;
      }
    }, 500);
  });
}
