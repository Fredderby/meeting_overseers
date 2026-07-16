let currentCategory = window.location.pathname.split('/').pop();
let currentPage = 1;
let currentData = [];
let allData = [];

document.addEventListener('DOMContentLoaded', function() {
  loadPeople();
  setupSidebar();
  setupSearch();
  setupSelectAll();
});

async function loadPeople() {
  try {
    const res = await fetch(`/api/people/${currentCategory}`);
    const data = await res.json();
    allData = data;
    renderTable(data);
  } catch (err) {
    showToast('Failed to load people', 'error');
  }
}

function renderTable(data) {
  const tbody = document.getElementById('tableBody');
  document.getElementById('totalCount').textContent = data.length;

  tbody.innerHTML = data.map(p => `
    <tr>
      <td><input type="checkbox" class="row-check" value="${p.id}"></td>
      <td><strong>${escapeHtml(p.name)}</strong></td>
      <td>${escapeHtml(p.designation || '-')}</td>
      <td>${escapeHtml(p.phone_number || '-')}</td>
      <td>${escapeHtml(p.region_division || '-')}</td>
      <td><span class="status-badge ${p.verification_status === 'Verified' ? 'status-verified' : 'status-pending'}">${p.verification_status}</span></td>
      <td>
        <button class="btn btn-sm" onclick="openEditModal(${p.id})">Edit</button>
        <button class="btn btn-sm btn-danger" onclick="deletePerson(${p.id})">Delete</button>
      </td>
    </tr>
  `).join('');
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function openAddModal() {
  document.getElementById('addModal').classList.add('show');
  document.getElementById('addForm').reset();
}

function closeModal(id) {
  document.getElementById(id).classList.remove('show');
}

function openEditModal(personId) {
  const person = allData.find(p => p.id === personId);
  if (!person) return;
  document.getElementById('editId').value = person.id;
  document.getElementById('editName').value = person.name || '';
  document.getElementById('editDesignation').value = person.designation || '';
  document.getElementById('editPhone').value = person.phone_number || '';
  document.getElementById('editRegion').value = person.region_division || '';
  document.getElementById('editRemarks').value = person.remarks || '';
  document.getElementById('editModal').classList.add('show');
}

async function addPerson(e) {
  e.preventDefault();
  const form = document.getElementById('addForm');
  const formData = new FormData(form);

  try {
    const res = await fetch(`/api/people/${currentCategory}/add`, {
      method: 'POST',
      body: formData,
    });
    if (res.ok) {
      showToast('Person added successfully', 'success');
      closeModal('addModal');
      loadPeople();
    } else {
      const data = await res.json();
      showToast(data.detail || 'Failed to add person', 'error');
    }
  } catch (err) {
    showToast('Connection error', 'error');
  }
}

async function editPerson(e) {
  e.preventDefault();
  const form = document.getElementById('editForm');
  const formData = new FormData(form);
  const personId = document.getElementById('editId').value;

  try {
    const res = await fetch(`/api/people/${currentCategory}/${personId}`, {
      method: 'PUT',
      body: formData,
    });
    if (res.ok) {
      showToast('Person updated successfully', 'success');
      closeModal('editModal');
      loadPeople();
    } else {
      const data = await res.json();
      showToast(data.detail || 'Failed to update', 'error');
    }
  } catch (err) {
    showToast('Connection error', 'error');
  }
}

async function deletePerson(personId) {
  if (!confirm('Are you sure you want to delete this person?')) return;
  try {
    const res = await fetch(`/api/people/${currentCategory}/${personId}`, {
      method: 'DELETE',
    });
    if (res.ok) {
      showToast('Person deleted', 'success');
      loadPeople();
    }
  } catch (err) {
    showToast('Failed to delete', 'error');
  }
}

function setupSearch() {
  const input = document.getElementById('tableSearch');
  if (!input) return;

  input.addEventListener('input', function() {
    const q = this.value.toLowerCase();
    const filtered = allData.filter(p =>
      (p.name && p.name.toLowerCase().includes(q)) ||
      (p.designation && p.designation.toLowerCase().includes(q)) ||
      (p.phone_number && p.phone_number.toLowerCase().includes(q)) ||
      (p.region_division && p.region_division.toLowerCase().includes(q))
    );
    renderTable(filtered);
  });
}

function setupSelectAll() {
  const selectAll = document.getElementById('selectAll');
  if (!selectAll) return;

  selectAll.addEventListener('change', function() {
    document.querySelectorAll('.row-check').forEach(cb => cb.checked = this.checked);
  });
}

function bulkDelete() {
  const checked = document.querySelectorAll('.row-check:checked');
  if (checked.length === 0) return showToast('Select records first', 'warning');
  if (!confirm(`Delete ${checked.length} records?`)) return;

  const ids = Array.from(checked).map(cb => cb.value).join(',');
  const formData = new FormData();
  formData.append('ids', ids);
  formData.append('action', 'delete');

  fetch(`/api/people/${currentCategory}/bulk`, { method: 'POST', body: formData })
    .then(res => res.json())
    .then(data => {
      showToast(`Deleted ${data.count} records`, 'success');
      loadPeople();
    });
}

function exportTable() {
  window.location.href = `/api/export/${currentCategory === 'men' ? 'men' : currentCategory === 'women' ? 'women' : 'stakeholders'}`;
}

function sortTable(col) {
  allData.sort((a, b) => {
    const av = (a[col] || '').toLowerCase();
    const bv = (b[col] || '').toLowerCase();
    return av.localeCompare(bv);
  });
  renderTable(allData);
}

function setupSidebar() {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
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
