let currentFilePath = '';
let currentCategory = 'Men';

document.addEventListener('DOMContentLoaded', function() {
  setupDropzone();
  setupFileInput();
  setupSidebar();
});

function setupDropzone() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');

  dropzone.addEventListener('click', function() {
    fileInput.click();
  });

  dropzone.addEventListener('dragover', function(e) {
    e.preventDefault();
    this.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', function() {
    this.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', function(e) {
    e.preventDefault();
    this.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      handleFile(e.dataTransfer.files[0]);
    }
  });
}

function setupFileInput() {
  const fileInput = document.getElementById('fileInput');
  fileInput.addEventListener('change', function() {
    if (this.files.length) {
      handleFile(this.files[0]);
    }
  });
}

function handleFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['xlsx', 'xls', 'csv'].includes(ext)) {
    showToast('Invalid file format. Use .xlsx, .xls, or .csv', 'error');
    return;
  }

  previewFile(file);
}

async function previewFile(file) {
  currentCategory = document.getElementById('uploadCategory').value;
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', currentCategory);

  showToast('Analyzing file...', 'info');

  try {
    const res = await fetch('/api/upload/preview', {
      method: 'POST',
      body: formData,
    });

    if (res.ok) {
      const data = await res.json();
      currentFilePath = data.file_path;
      showPreview(data);
    } else {
      const err = await res.json();
      showToast(err.detail || 'File validation failed', 'error');
    }
  } catch (err) {
    showToast('Failed to process file', 'error');
  }
}

function showPreview(data) {
  document.getElementById('uploadOptions').style.display = 'flex';
  document.getElementById('previewArea').style.display = 'block';
  document.getElementById('resultArea').style.display = 'none';

  const summary = document.getElementById('uploadSummary');
  summary.innerHTML = `
    <div class="stat"><div class="label">Total Records</div><div class="value">${data.total_records}</div></div>
    <div class="stat"><div class="label">Duplicates</div><div class="value">${data.duplicate_count}</div></div>
  `;

  const table = document.getElementById('previewTable');
  const thead = table.querySelector('thead');
  const tbody = table.querySelector('tbody');

  if (data.preview && data.preview.length > 0 && data.columns.length > 0) {
    const headers = data.columns;
    thead.innerHTML = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
    tbody.innerHTML = data.preview.slice(0, 5).map(row =>
      `<tr>${headers.map(h => `<td>${row[h] || ''}</td>`).join('')}</tr>`
    ).join('');
  }

  if (data.duplicates && data.duplicates.length > 0) {
    summary.innerHTML += `
      <div class="stat" style="border-left: 3px solid #f59e0b;">
        <div class="label">Duplicate Names</div>
        <div class="value">${data.duplicates.slice(0, 5).map(d => d.existing_name).join(', ')}${data.duplicates.length > 5 ? '...' : ''}</div>
      </div>
    `;
  }
}

async function importData() {
  if (!currentFilePath) return;

  const formData = new FormData();
  formData.append('file_path', currentFilePath);
  formData.append('category', currentCategory);
  formData.append('overwrite', document.getElementById('overwriteCheck').checked ? 'true' : 'false');
  formData.append('ignore_duplicates', document.getElementById('ignoreDuplicates').checked ? 'true' : 'false');

  document.getElementById('importBtn').disabled = true;
  document.getElementById('importBtn').textContent = 'Importing...';

  try {
    const res = await fetch('/api/upload/import', {
      method: 'POST',
      body: formData,
    });

    const data = await res.json();
    const resultArea = document.getElementById('resultArea');
    resultArea.style.display = 'block';

    if (data.success) {
      resultArea.innerHTML = `
        <h3 style="color: #10b981;">Import Complete</h3>
        <p>Successfully imported <strong>${data.imported}</strong> records.</p>
        <p>Skipped: <strong>${data.skipped}</strong></p>
        ${data.errors.length ? `<div style="margin-top:12px"><strong>Errors:</strong><ul style="margin-top:4px">${data.errors.map(e => `<li style="font-size:13px;color:#ef4444">${e}</li>`).join('')}</ul></div>` : ''}
      `;
      showToast(`Imported ${data.imported} records`, 'success');
    } else {
      resultArea.innerHTML = `<h3 style="color: #ef4444;">Import Failed</h3><p>${data.error || 'Unknown error'}</p>`;
      showToast('Import failed', 'error');
    }
  } catch (err) {
    showToast('Import error', 'error');
  } finally {
    document.getElementById('importBtn').disabled = false;
    document.getElementById('importBtn').textContent = 'Import to Database';
  }
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
