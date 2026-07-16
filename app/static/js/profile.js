document.addEventListener('DOMContentLoaded', function() {
  setupSidebar();
});

async function updateProfile(e) {
  e.preventDefault();
  const form = document.getElementById('profileForm');
  const formData = new FormData(form);

  try {
    const res = await fetch('/api/profile/update', { method: 'POST', body: formData });
    if (res.ok) {
      showToast('Profile updated successfully', 'success');
    } else {
      showToast('Failed to update profile', 'error');
    }
  } catch (err) {
    showToast('Connection error', 'error');
  }
}

async function changePassword(e) {
  e.preventDefault();
  const form = document.getElementById('passwordForm');
  const formData = new FormData(form);

  if (formData.get('new_password') !== formData.get('confirm_password')) {
    showToast('Passwords do not match', 'error');
    return;
  }

  try {
    const res = await fetch('/api/profile/password', { method: 'POST', body: formData });
    if (res.ok) {
      showToast('Password changed successfully', 'success');
      form.reset();
    } else {
      const data = await res.json();
      showToast(data.detail || 'Failed to change password', 'error');
    }
  } catch (err) {
    showToast('Connection error', 'error');
  }
}

async function uploadPic(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/profile/picture', { method: 'POST', body: formData });
    if (res.ok) {
      showToast('Profile picture updated', 'success');
      location.reload();
    }
  } catch (err) {
    showToast('Failed to upload picture', 'error');
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
