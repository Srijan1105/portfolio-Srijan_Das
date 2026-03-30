// ── Theme Toggle ──────────────────────────────────────────────────────────────
const themeToggle = document.getElementById('themeToggle');
const iconMoon    = themeToggle.querySelector('.icon-moon');
const iconSun     = themeToggle.querySelector('.icon-sun');

function applyTheme(theme) {
  if (theme === 'light') {
    document.body.classList.add('light');
    iconMoon.style.display = 'none';
    iconSun.style.display  = 'block';
  } else {
    document.body.classList.remove('light');
    iconMoon.style.display = 'block';
    iconSun.style.display  = 'none';
  }
}

// Load saved preference, default to dark
applyTheme(localStorage.getItem('theme') || 'dark');

themeToggle.addEventListener('click', () => {
  const next = document.body.classList.contains('light') ? 'dark' : 'light';
  localStorage.setItem('theme', next);
  applyTheme(next);
});

// Nav scroll effect
const roles = ['Data Scientist', 'Software Engineer', 'Java Developer', 'Machine Learning Engineer', 'Python Developer', 'Data Analyst', 'SQL Developer'];
let roleIndex = 0, charIndex = 0, isDeleting = false;
const typedEl = document.getElementById('typedText');

function type() {
  const current = roles[roleIndex];
  typedEl.textContent = isDeleting ? current.slice(0, charIndex--) : current.slice(0, charIndex++);

  let delay = isDeleting ? 60 : 100;

  if (!isDeleting && charIndex > current.length) {
    isDeleting = true;
    delay = 1800; // pause before deleting
  } else if (isDeleting && charIndex < 0) {
    isDeleting = false;
    charIndex = 0;
    roleIndex = (roleIndex + 1) % roles.length;
    delay = 400;
  }
  setTimeout(type, delay);
}
type();


const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 20);
});

// Hamburger menu
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');

hamburger.addEventListener('click', () => {
  mobileMenu.classList.toggle('open');
});

// Close mobile menu on link click
mobileMenu.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => mobileMenu.classList.remove('open'));
});

// Smooth active nav link highlight
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-links a, .mobile-menu a');

window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(section => {
    if (window.scrollY >= section.offsetTop - 80) current = section.id;
  });
  navLinks.forEach(link => {
    link.style.color = link.getAttribute('href') === `#${current}` ? 'var(--accent-light)' : '';
  });
});

// Intersection Observer for fade-in animations
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.skill-card, .project-card, .timeline-item, .about-grid, .contact-grid')
  .forEach(el => {
    el.classList.add('fade-in');
    observer.observe(el);
  });

// Contact form
const form = document.getElementById('contactForm');
const successMsg = document.getElementById('formSuccess');

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const btn = form.querySelector('button[type="submit"]');
  btn.textContent = 'Sending...';
  btn.disabled = true;

  // Simulate send (replace with real API call)
  setTimeout(() => {
    form.reset();
    btn.textContent = 'Send Message';
    btn.disabled = false;
    successMsg.classList.add('show');
    setTimeout(() => successMsg.classList.remove('show'), 4000);
  }, 1200);
});

// Footer year
document.getElementById('year').textContent = new Date().getFullYear();

// ── Resume Request Modal ──────────────────────────────────────────────────────
const BACKEND = '';

const resumeBtn   = document.getElementById('resumeBtn');
const resumeModal = document.getElementById('resumeModal');
const modalClose  = document.getElementById('modalClose');
const reqForm     = document.getElementById('resumeRequestForm');
const reqSuccess  = document.getElementById('reqSuccess');
const reqError    = document.getElementById('reqError');
const reqSubmitBtn = document.getElementById('reqSubmitBtn');

resumeBtn.addEventListener('click', (e) => {
  e.preventDefault();
  resumeModal.classList.add('open');
});

modalClose.addEventListener('click', () => resumeModal.classList.remove('open'));

resumeModal.addEventListener('click', (e) => {
  if (e.target === resumeModal) resumeModal.classList.remove('open');
});

reqForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  reqSuccess.classList.remove('show');
  reqError.classList.remove('show');

  const name   = document.getElementById('reqName').value.trim();
  const email  = document.getElementById('reqEmail').value.trim();
  const reason = document.getElementById('reqReason').value.trim();

  reqSubmitBtn.textContent = 'Submitting...';
  reqSubmitBtn.disabled = true;

  try {
    const res  = await fetch(`${BACKEND}/api/request-resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, reason }),
    });
    const data = await res.json();

    if (!res.ok) {
      reqError.textContent = data.error || 'Something went wrong.';
      reqError.classList.add('show');
    } else {
      reqSuccess.textContent = data.verified
        ? '✅ ' + data.message
        : '📩 ' + data.message;
      reqSuccess.classList.add('show');
      reqForm.reset();
    }
  } catch {
    reqError.textContent = 'Could not reach the server. Please try again.';
    reqError.classList.add('show');
  } finally {
    reqSubmitBtn.textContent = 'Submit Request';
    reqSubmitBtn.disabled = false;
  }
});

// ── LeetCode Stats ────────────────────────────────────────────────────────────
async function loadLeetCode() {
  try {
    const res  = await fetch('/api/leetcode');
    const data = await res.json();

    if (data.error) throw new Error(data.error);

    document.getElementById('lcUsername').textContent    = data.username;
    document.getElementById('lcTotal').textContent       = data.totalSolved;
    document.getElementById('lcEasy').textContent        = data.easySolved;
    document.getElementById('lcMedium').textContent      = data.mediumSolved;
    document.getElementById('lcHard').textContent        = data.hardSolved;
    document.getElementById('lcStreak').textContent      = data.streak;
    document.getElementById('lcActiveDays').textContent  = data.totalActiveDays;
    document.getElementById('lcContests').textContent    = data.contestsAttended;
    document.getElementById('lcRating').textContent      = data.contestRating || '—';

    const rankEl = document.getElementById('lcRank');
    rankEl.innerHTML = data.ranking
      ? `Global Rank: #${data.ranking.toLocaleString()}`
      : (data.contestGlobalRanking !== 'N/A' ? `Contest Rank: #${data.contestGlobalRanking}` : 'Unranked');

    // Badges
    if (data.badges && data.badges.length > 0) {
      const wrap = document.getElementById('lcBadgesWrap');
      const container = document.getElementById('lcBadges');
      wrap.style.display = 'block';
      container.innerHTML = data.badges.map(b => `
        <div class="lc-badge">
          ${b.icon ? `<img src="${b.icon}" alt="${b.name}" onerror="this.style.display='none'">` : '🏅'}
          <span>${b.name}</span>
        </div>
      `).join('');
    }

  } catch (err) {
    const errEl = document.getElementById('lcError');
    errEl.textContent = 'Could not load LeetCode stats. Try refreshing.';
    errEl.style.display = 'block';
    console.error('LeetCode fetch error:', err);
  }
}

loadLeetCode();

// ── View Counter (polling) ────────────────────────────────────────────────────
(function () {
  const el = document.getElementById('viewCount');
  let lastCount = 0;

  function animateCount(from, to) {
    if (from === to) { el.textContent = to.toLocaleString(); return; }
    const step = Math.ceil(Math.abs(to - from) / 20);
    let cur = from;
    const timer = setInterval(() => {
      cur = cur < to ? Math.min(cur + step, to) : Math.max(cur - step, to);
      el.textContent = cur.toLocaleString();
      if (cur === to) clearInterval(timer);
    }, 30);
  }

  // Track this visit and get initial count
  fetch('/api/views/track', { method: 'POST' })
    .then(r => r.json())
    .then(d => { animateCount(lastCount, d.total); lastCount = d.total; })
    .catch(() => {});

  // Poll every 15s to reflect other visitors in real time
  setInterval(() => {
    fetch('/api/views')
      .then(r => r.json())
      .then(d => {
        if (d.total !== lastCount) {
          animateCount(lastCount, d.total);
          lastCount = d.total;
        }
      })
      .catch(() => {});
  }, 15000);
})();

// ── GitHub Repo Count ─────────────────────────────────────────────────────────
async function fetchRepoCount() {
  try {
    const res  = await fetch('https://api.github.com/users/Srijan1105');
    const data = await res.json();
    const count = data.public_repos;
    if (count) document.getElementById('repoCount').textContent = count + '+';
  } catch {}
}

fetchRepoCount();
setInterval(fetchRepoCount, 5 * 60 * 1000); // re-check every 5 minutes

// ── GitHub Projects with Filter ───────────────────────────────────────────────
const GITHUB_SVG = `<svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>`;
const LINK_SVG   = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`;

let allRepos = [];
let activeFilter = 'All';

function getLangIcon(lang) {
  const icons = { Python:'🐍', Java:'☕', JavaScript:'🟨', HTML:'🌐', CSS:'🎨', 'Jupyter Notebook':'📓' };
  return icons[lang] || '💻';
}

function renderProjects(filter) {
  const grid = document.getElementById('projectsGrid');
  const search = (document.getElementById('projectSearch')?.value || '').toLowerCase();

  const filtered = allRepos.filter(r => {
    const matchFilter = filter === 'All' || r.categories.includes(filter);
    const matchSearch = !search ||
      r.name.toLowerCase().includes(search) ||
      r.description.toLowerCase().includes(search) ||
      r.language.toLowerCase().includes(search) ||
      r.topics.some(t => t.toLowerCase().includes(search));
    return matchFilter && matchSearch;
  });

  if (!filtered.length) {
    grid.innerHTML = `<p class="projects-loading">No ${filter} projects found.</p>`;
    return;
  }

  grid.innerHTML = filtered.map((r, i) => `
    <div class="project-card fade-in" style="animation-delay:${i * 0.05}s">
      <div class="project-header">
        <div class="project-icon">${getLangIcon(r.language)}</div>
        <div class="project-links">
          <a href="${r.url}" target="_blank" rel="noopener" aria-label="GitHub repo">${GITHUB_SVG}</a>
          ${r.homepage ? `<a href="${r.homepage}" target="_blank" rel="noopener" aria-label="Live demo">${LINK_SVG}</a>` : ''}
        </div>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        ${r.categories.map(c => `<span class="project-cat-badge">${c}</span>`).join('')}
      </div>
      <h3 class="project-title">${r.name.replace(/-/g, ' ')}</h3>
      <p class="project-desc">${r.description || 'No description provided.'}</p>
      <div class="project-tags">
        ${r.language ? `<span>${r.language}</span>` : ''}
        ${r.topics.slice(0, 4).map(t => `<span>${t}</span>`).join('')}
      </div>
    </div>
  `).join('');

  // Re-observe new cards for fade-in
  grid.querySelectorAll('.fade-in').forEach(el => {
    el.classList.add('visible');
  });
}

async function loadProjects() {
  try {
    const res  = await fetch('/api/github-repos');
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    allRepos = data;
    renderProjects('All');
  } catch (e) {
    document.getElementById('projectsGrid').innerHTML =
      `<p class="projects-loading">Could not load projects. <a href="https://github.com/Srijan1105" target="_blank" style="color:var(--accent-light)">View on GitHub →</a></p>`;
  }
}

// Filter button clicks
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.filter;
    renderProjects(activeFilter);
  });
});

loadProjects();
