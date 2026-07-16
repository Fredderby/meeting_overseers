document.addEventListener('DOMContentLoaded', function() {
  createParticles();
  setupLoginForm();
  setupPasswordToggle();
});

function createParticles() {
  const container = document.getElementById('particles');
  if (!container) return;
  const count = 50;

  for (let i = 0; i < count; i++) {
    const particle = document.createElement('div');
    const size = Math.random() * 4 + 2;
    particle.style.cssText = `
      position: absolute;
      width: ${size}px;
      height: ${size}px;
      background: rgba(255, 255, 255, ${Math.random() * 0.3 + 0.1});
      border-radius: 50%;
      top: ${Math.random() * 100}%;
      left: ${Math.random() * 100}%;
      animation: floatParticle ${Math.random() * 10 + 10}s linear infinite;
      animation-delay: ${Math.random() * 5}s;
    `;
    container.appendChild(particle);
  }
}

const style = document.createElement('style');
style.textContent = `
  @keyframes floatParticle {
    0% { transform: translateY(0) translateX(0); opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { transform: translateY(-100vh) translateX(${Math.random() * 200 - 100}px); opacity: 0; }
  }
`;
document.head.appendChild(style);

function setupLoginForm() {
  const form = document.getElementById('loginForm');
  const btn = document.getElementById('loginBtn');
  const errorMsg = document.getElementById('errorMessage');

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    btn.classList.add('loading');
    errorMsg.classList.remove('visible');

    const formData = new FormData(form);
    formData.set('remember_me', document.getElementById('rememberMe').checked ? 'true' : 'false');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        window.location.href = data.redirect || '/dashboard';
      } else {
        const data = await res.json();
        errorMsg.textContent = data.error || 'Login failed';
        errorMsg.classList.add('visible');
        btn.classList.remove('loading');
      }
    } catch (err) {
      errorMsg.textContent = 'Connection error. Please try again.';
      errorMsg.classList.add('visible');
      btn.classList.remove('loading');
    }
  });
}

function setupPasswordToggle() {
  const toggle = document.getElementById('togglePassword');
  const password = document.getElementById('password');

  toggle.addEventListener('click', function() {
    const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
    password.setAttribute('type', type);
    toggle.innerHTML = type === 'password'
      ? '<svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>'
      : '<svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/></svg>';
  });
}
