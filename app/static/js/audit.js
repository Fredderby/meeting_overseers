let currentAuditPage = 1;

document.addEventListener('DOMContentLoaded', function() {
  loadAuditLogs();
  setupSidebar();
});

async function loadAuditLogs() {
  const action = document.getElementById('actionFilter').value;
  try {
    const res = await fetch(`/api/audit-logs?action=${action}&page=${currentAuditPage}&page_size=50`);
    const data = await res.json();
    renderAuditLogs(data.logs, data.total);
  } catch (err) {
    console.error('Failed to load audit logs', err);
  }
}

function renderAuditLogs(logs, total) {
  const tbody = document.getElementById('auditBody');
  tbody.innerHTML = logs.map(l => `
    <tr>
      <td>${l.username || 'System'}</td>
      <td><span class="status-badge ${getActionColor(l.action)}">${l.action}</span></td>
      <td>${l.entity_type || '-'}</td>
      <td>${l.details || '-'}</td>
      <td>${formatTime(l.timestamp)}</td>
    </tr>
  `).join('');

  const totalPages = Math.ceil(total / 50);
  const pagination = document.getElementById('auditPagination');
  let html = `<button ${currentAuditPage <= 1 ? 'disabled' : ''} onclick="changeAuditPage(${currentAuditPage - 1})">Previous</button>`;
  for (let i = 1; i <= totalPages && i <= 10; i++) {
    html += `<button class="${i === currentAuditPage ? 'active' : ''}" onclick="changeAuditPage(${i})">${i}</button>`;
  }
  html += `<button ${currentAuditPage >= totalPages ? 'disabled' : ''} onclick="changeAuditPage(${currentAuditPage + 1})">Next</button>`;
  pagination.innerHTML = html;
}

function changeAuditPage(page) {
  currentAuditPage = page;
  loadAuditLogs();
}

function getActionColor(action) {
  const colors = {
    'login': 'status-pending',
    'logout': 'status-pending',
    'upload': 'status-verified',
    'create': 'status-verified',
    'update': 'status-verified',
    'delete': '',
    'verify_attendance': 'status-verified',
    'export': 'status-verified',
  };
  return colors[action] || '';
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
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  }
}
