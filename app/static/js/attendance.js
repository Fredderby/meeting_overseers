document.addEventListener('DOMContentLoaded', function() {
  setupSidebar();
  setupCategoryTabs();
  setupSearch();
  loadParticipants();
  loadTodaySummary();
});

let allParticipants = [];
let activeCategory = '';
let searchQuery = '';

function setupCategoryTabs() {
  document.getElementById('categoryTabs').addEventListener('click', function(e) {
    const tab = e.target.closest('.category-tab');
    if (!tab) return;
    document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    activeCategory = tab.dataset.cat;
    renderParticipants();
  });
}

function setupSearch() {
  const input = document.getElementById('searchFilter');
  input.addEventListener('input', function() {
    searchQuery = this.value.trim().toLowerCase();
    renderParticipants();
  });
}

async function loadParticipants() {
  try {
    const res = await fetch('/api/attendance/participants');
    const data = await res.json();
    allParticipants = data.participants;
    renderParticipants();
    updateStats();
  } catch (err) {
    console.error('Failed to load participants', err);
  }
}

function renderParticipants() {
  const filtered = allParticipants.filter(p => {
    if (activeCategory && p.category !== activeCategory) return false;
    if (!searchQuery) return true;
    const q = searchQuery;
    return (p.name && p.name.toLowerCase().includes(q)) ||
           (p.designation && p.designation.toLowerCase().includes(q)) ||
           (p.region_division && p.region_division.toLowerCase().includes(q)) ||
           (p.phone_number && p.phone_number.toLowerCase().includes(q));
  });

  const container = document.getElementById('participantsList');
  if (filtered.length === 0) {
    container.innerHTML = '<div class="empty-state"><svg viewBox="0 0 24 24" width="48" height="48"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg><p>No participants found</p></div>';
    return;
  }

  container.innerHTML = filtered.map((p, i) => `
    <tr>
      <td class="col-index">${i + 1}</td>
      <td class="col-name"><span class="person-name">${escapeHtml(p.name)}</span></td>
      <td class="col-desig">${escapeHtml(p.designation) || '<span class="muted">—</span>'}</td>
      <td class="col-region">${escapeHtml(p.region_division) || '<span class="muted">—</span>'}</td>
      <td class="col-phone">${escapeHtml(p.phone_number) || '<span class="muted">—</span>'}</td>
      <td class="col-cat"><span class="cat-badge cat-${p.category.toLowerCase()}">${p.category}</span></td>
      <td class="col-status">${p.verified
        ? '<span class="status-badge status-verified"><svg viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg> Verified</span>'
        : '<span class="status-badge status-pending"><svg viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg> Pending</span>'}</td>
      <td class="col-time">${p.verification_time ? formatTime(p.verification_time) : '<span class="muted">—</span>'}</td>
      <td class="col-actions">
        <div class="action-btns">
          ${p.verified
            ? `<button class="btn-action btn-verified" disabled title="Verified"><svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></button>`
            : `<button class="btn-action btn-verify" onclick="toggleVerify(${p.id},'${p.category}')" title="Mark Present"><svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></button>`}
          <button class="btn-action btn-edit" onclick="openEditModal(${p.id},'${p.category}','${escapeJs(p.name)}','${escapeJs(p.designation||'')}','${escapeJs(p.region_division||'')}','${escapeJs(p.phone_number||'')}')" title="Edit"><svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg></button>
        </div>
      </td>
    </tr>
  `).join('');
}

function updateStats() {
  const total = allParticipants.length;
  const verified = allParticipants.filter(p => p.verified).length;
  document.getElementById('statTotal').textContent = total;
  document.getElementById('statVerified').textContent = verified;
  document.getElementById('statPending').textContent = total - verified;
}

async function toggleVerify(personId, category) {
  const formData = new FormData();
  formData.set('person_id', personId);
  formData.set('person_category', category);

  try {
    const res = await fetch('/api/attendance/verify', { method: 'POST', body: formData });
    const data = await res.json();
    if (res.ok) {
      const p = allParticipants.find(x => x.id === personId && x.category === category);
      if (p) { p.verified = true; p.verification_time = data.attendance?.time || new Date().toISOString(); }
      renderParticipants();
      updateStats();
      loadTodaySummary();
      showToast('Attendance verified successfully', 'success');
    } else {
      showToast(data.error || 'Verification failed', 'error');
    }
  } catch (err) {
    showToast('Connection error', 'error');
  }
}

async function saveEdit(personId, category) {
  const name = document.getElementById('editName').value.trim();
  if (!name) { showToast('Name is required', 'error'); return; }

  const formData = new FormData();
  formData.set('name', name);
  formData.set('designation', document.getElementById('editDesignation').value.trim());
  formData.set('region_division', document.getElementById('editRegion').value.trim());
  formData.set('phone_number', document.getElementById('editPhone').value.trim());
  formData.set('remarks', '');

  const catMap = { 'Men': 'men', 'Women': 'women', 'Stakeholders': 'stakeholders' };
  const catLower = catMap[category] || 'men';

  try {
    const res = await fetch(`/api/people/${catLower}/${personId}`, { method: 'PUT', body: formData });
    if (res.ok) {
      const p = allParticipants.find(x => x.id === personId && x.category === category);
      if (p) { p.name = name; p.designation = document.getElementById('editDesignation').value.trim(); p.region_division = document.getElementById('editRegion').value.trim(); p.phone_number = document.getElementById('editPhone').value.trim(); }
      renderParticipants();
      closeEditModal();
      showToast('Person updated successfully', 'success');
    } else {
      const data = await res.json();
      showToast(data.detail || 'Update failed', 'error');
    }
  } catch (err) {
    showToast('Connection error', 'error');
  }
}

function openEditModal(id, category, name, designation, region, phone) {
  document.getElementById('editId').value = id;
  document.getElementById('editCategory').value = category;
  document.getElementById('editName').value = name;
  document.getElementById('editDesignation').value = designation;
  document.getElementById('editRegion').value = region;
  document.getElementById('editPhone').value = phone;
  document.getElementById('editModal').classList.add('show');
  document.getElementById('editName').focus();
}

function closeEditModal() {
  document.getElementById('editModal').classList.remove('show');
}

async function loadTodaySummary() {
  try {
    const res = await fetch('/api/attendance/today');
    const data = await res.json();
    const container = document.getElementById('todaySummary');
    if (!data.logs || data.logs.length === 0) {
      container.innerHTML = '<div class="summary-empty">No verifications yet today</div>';
      return;
    }
    container.innerHTML = data.logs.map(l => `
      <div class="summary-item">
        <span class="summary-name">${escapeHtml(l.person_name)}</span>
        <span class="summary-time">${formatTime(l.verification_time)}</span>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load today summary', err);
  }
}

function formatTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function escapeJs(text) {
  return text.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function setupSidebar() {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const backdrop = document.getElementById('sidebarBackdrop');
  function toggleSidebar() {
    const isOpen = sidebar.classList.toggle('open');
    if (backdrop) backdrop.classList.toggle('show', isOpen);
  }
  if (toggle && sidebar) {
    toggle.addEventListener('click', toggleSidebar);
  }
  if (backdrop) {
    backdrop.addEventListener('click', function() {
      sidebar.classList.remove('open');
      backdrop.classList.remove('show');
    });
  }
}

function showToast(message, type) {
  const container = document.querySelector('.toast-container') || createToastContainer();
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

function createToastContainer() {
  const container = document.createElement('div');
  container.className = 'toast-container';
  document.body.appendChild(container);
  return container;
}

document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) closeEditModal();
});
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeEditModal();
});
