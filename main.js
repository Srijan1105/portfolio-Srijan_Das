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
  if (!isDeleting && charIndex > current.length) { isDeleting = true; delay = 1800; }
  else if (isDeleting && charIndex < 0) { isDeleting = false; charIndex = 0; roleIndex = (roleIndex + 1) % roles.length; delay = 400; }
  setTimeout(type, delay);
}
type();

const nav = document.getElementById('nav');
window.addEventListener('scroll', () => nav.classList.toggle('scrolled', window.scrollY > 20));

const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');
hamburger.addEventListener('click', () => mobileMenu.classList.toggle('open'));
mobileMenu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => mobileMenu.classList.remove('open')));

const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-links a, .mobile-menu a');
window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(section => { if (window.scrollY >= section.offsetTop - 80) current = section.id; });
  navLinks.forEach(link => { link.style.color = link.getAttribute('href') === `#${current}` ? 'var(--accent-light)' : ''; });
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); } });
}, { threshold: 0.1 });
document.querySelectorAll('.skill-card, .project-card, .timeline-item, .about-grid, .contact-grid')
  .forEach(el => { el.classList.add('fade-in'); observer.observe(el); });

const form = document.getElementById('contactForm');
const successMsg = document.getElementById('formSuccess');
form.addEventListener('submit', (e) => {
  e.preventDefault();
  const btn = form.querySelector('button[type="submit"]');
  btn.textContent = 'Sending...'; btn.disabled = true;
  setTimeout(() => { form.reset(); btn.textContent = 'Send Message'; btn.disabled = false; successMsg.classList.add('show'); setTimeout(() => successMsg.classList.remove('show'), 4000); }, 1200);
});

document.getElementById('year').textContent = new Date().getFullYear();

// ── Resume Request Modal ──────────────────────────────────────────────────────
const BACKEND = '';
const resumeBtn    = document.getElementById('resumeBtn');
const resumeModal  = document.getElementById('resumeModal');
const modalClose   = document.getElementById('modalClose');
const reqForm      = document.getElementById('resumeRequestForm');
const reqSuccess   = document.getElementById('reqSuccess');
const reqError     = document.getElementById('reqError');
const reqSubmitBtn = document.getElementById('reqSubmitBtn');

resumeBtn.addEventListener('click', (e) => { e.preventDefault(); resumeModal.classList.add('open'); });
modalClose.addEventListener('click', () => resumeModal.classList.remove('open'));
resumeModal.addEventListener('click', (e) => { if (e.target === resumeModal) resumeModal.classList.remove('open'); });

reqForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  reqSuccess.classList.remove('show'); reqError.classList.remove('show');
  const name = document.getElementById('reqName').value.trim();
  const email = document.getElementById('reqEmail').value.trim();
  const reason = document.getElementById('reqReason').value.trim();
  reqSubmitBtn.textContent = 'Submitting...'; reqSubmitBtn.disabled = true;
  try {
    const res = await fetch(`${BACKEND}/api/request-resume`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, email, reason }) });
    const data = await res.json();
    if (!res.ok) { reqError.textContent = data.error || 'Something went wrong.'; reqError.classList.add('show'); }
    else { reqSuccess.textContent = data.verified ? '✅ ' + data.message : '📩 ' + data.message; reqSuccess.classList.add('show'); reqForm.reset(); }
  } catch { reqError.textContent = 'Could not reach the server. Please try again.'; reqError.classList.add('show'); }
  finally { reqSubmitBtn.textContent = 'Submit Request'; reqSubmitBtn.disabled = false; }
});

// ── LeetCode Stats ────────────────────────────────────────────────────────────
async function loadLeetCode() {
  try {
    const res = await fetch('/api/leetcode');
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    document.getElementById('lcUsername').textContent   = data.username;
    document.getElementById('lcTotal').textContent      = data.totalSolved;
    document.getElementById('lcEasy').textContent       = data.easySolved;
    document.getElementById('lcMedium').textContent     = data.mediumSolved;
    document.getElementById('lcHard').textContent       = data.hardSolved;
    document.getElementById('lcStreak').textContent     = data.streak;
    document.getElementById('lcActiveDays').textContent = data.totalActiveDays;
    document.getElementById('lcContests').textContent   = data.contestsAttended;
    document.getElementById('lcRating').textContent     = data.contestRating || '—';
    const rankEl = document.getElementById('lcRank');
    rankEl.innerHTML = data.ranking ? `Global Rank: #${data.ranking.toLocaleString()}` : (data.contestGlobalRanking !== 'N/A' ? `Contest Rank: #${data.contestGlobalRanking}` : 'Unranked');
    if (data.badges && data.badges.length > 0) {
      const wrap = document.getElementById('lcBadgesWrap');
      const container = document.getElementById('lcBadges');
      wrap.style.display = 'block';
      container.innerHTML = data.badges.map(b => `<div class="lc-badge">${b.icon ? `<img src="${b.icon}" alt="${b.name}" onerror="this.style.display='none'">` : '🏅'}<span>${b.name}</span></div>`).join('');
    }
  } catch (err) {
    const errEl = document.getElementById('lcError');
    errEl.textContent = 'Could not load LeetCode stats. Try refreshing.';
    errEl.style.display = 'block';
  }
}
loadLeetCode();

// ── View Counter ──────────────────────────────────────────────────────────────
(function () {
  const el = document.getElementById('viewCount');
  let lastCount = 0;
  function animateCount(from, to) {
    if (from === to) { el.textContent = to.toLocaleString(); return; }
    const step = Math.ceil(Math.abs(to - from) / 20);
    let cur = from;
    const timer = setInterval(() => { cur = cur < to ? Math.min(cur + step, to) : Math.max(cur - step, to); el.textContent = cur.toLocaleString(); if (cur === to) clearInterval(timer); }, 30);
  }
  fetch('/api/views/track', { method: 'POST' }).then(r => r.json()).then(d => { animateCount(lastCount, d.total); lastCount = d.total; }).catch(() => {});
  setInterval(() => { fetch('/api/views').then(r => r.json()).then(d => { if (d.total !== lastCount) { animateCount(lastCount, d.total); lastCount = d.total; } }).catch(() => {}); }, 15000);
})();

// ── GitHub Repo Count ─────────────────────────────────────────────────────────
async function fetchRepoCount() {
  try {
    const res = await fetch('https://api.github.com/users/Srijan1105');
    const data = await res.json();
    if (data.public_repos) document.getElementById('repoCount').textContent = data.public_repos + '+';
  } catch {}
}
fetchRepoCount();
setInterval(fetchRepoCount, 5 * 60 * 1000);

// ── GitHub Projects — Advanced Filter ────────────────────────────────────────
const GITHUB_SVG = `<svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>`;
const LINK_SVG   = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`;

let allRepos = [];
let activeFilter = 'All';

const LANG_ICONS = { Python:'🐍', Java:'☕', JavaScript:'🟨', HTML:'🌐', CSS:'🎨', 'Jupyter Notebook':'📓', TypeScript:'🔷', 'C++':'⚙️', C:'⚙️', Dart:'🎯' };

function getLangIcon(lang) { return LANG_ICONS[lang] || '💻'; }

function getFilterValues() {
  return {
    category: activeFilter,
    search: (document.getElementById('projectSearch')?.value || '').toLowerCase().trim(),
    lang: document.getElementById('langFilter')?.value || '',
    sort: document.getElementById('sortFilter')?.value || 'updated',
  };
}

function renderProjects() {
  const grid = document.getElementById('projectsGrid');
  const { category, search, lang, sort } = getFilterValues();

  let filtered = allRepos.filter(r => {
    const matchCat    = category === 'All' ? r.featured : r.categories.includes(category);
    const matchLang   = !lang || r.language === lang;
    const matchSearch = !search ||
      r.name.toLowerCase().includes(search) ||
      r.description.toLowerCase().includes(search) ||
      (r.language || '').toLowerCase().includes(search) ||
      r.topics.some(t => t.toLowerCase().includes(search));
    return matchCat && matchLang && matchSearch;
  });

  if (sort === 'stars')    filtered.sort((a, b) => b.stars - a.stars);
  else if (sort === 'name') filtered.sort((a, b) => a.name.localeCompare(b.name));

  const countEl = document.getElementById('resultCount');
  if (countEl) countEl.innerHTML = `Showing <span>${filtered.length}</span> of <span>${allRepos.length}</span> projects`;

  if (!filtered.length) {
    grid.innerHTML = `<p class="projects-loading">No projects match your filters. <button onclick="resetFilters()" style="color:var(--accent-light);background:none;border:none;cursor:pointer;font-size:0.9rem;">Clear filters</button></p>`;
    return;
  }

  grid.innerHTML = filtered.map((r, i) => `
    <div class="project-card fade-in">
      <div class="project-header">
        <div class="project-icon">${getLangIcon(r.language)}</div>
        <div class="project-links">
          <a href="${r.url}" target="_blank" rel="noopener" aria-label="GitHub">${GITHUB_SVG}</a>
          ${r.homepage ? `<a href="${r.homepage}" target="_blank" rel="noopener" aria-label="Live demo">${LINK_SVG}</a>` : ''}
        </div>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:2px">
        ${r.categories.map(c => `<span class="project-cat-badge">${c}</span>`).join('')}
        ${r.stars > 0 ? `<span class="project-cat-badge" style="margin-left:auto;background:rgba(251,191,36,0.1);color:#fbbf24;border-color:rgba(251,191,36,0.3)">⭐ ${r.stars}</span>` : ''}
      </div>
      <h3 class="project-title">${r.name.replace(/-|_/g, ' ')}</h3>
      <p class="project-desc">${r.description}</p>
      <div class="project-tags">
        ${r.language ? `<span>${r.language}</span>` : ''}
        ${r.topics.slice(0, 4).map(t => `<span>${t}</span>`).join('')}
      </div>
      <p style="font-size:0.72rem;color:var(--text-dim);margin-top:4px;font-family:'Fira Code',monospace">Updated: ${r.updated}</p>
    </div>
  `).join('');

  grid.querySelectorAll('.fade-in').forEach(el => el.classList.add('visible'));
}

function resetFilters() {
  document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
  document.querySelector('.filter-pill[data-filter="All"]').classList.add('active');
  activeFilter = 'All';
  const searchEl = document.getElementById('projectSearch');
  if (searchEl) searchEl.value = '';
  const clearBtn = document.getElementById('clearSearch');
  if (clearBtn) clearBtn.style.display = 'none';
  const langSel = document.getElementById('langFilter');
  if (langSel) langSel.value = '';
  renderProjects();
}

function populateLangFilter() {
  const langs = [...new Set(allRepos.map(r => r.language).filter(Boolean))].sort();
  const sel = document.getElementById('langFilter');
  if (!sel) return;
  langs.forEach(l => { const opt = document.createElement('option'); opt.value = l; opt.textContent = l; sel.appendChild(opt); });
}

async function loadProjects() {
  try {
    const res = await fetch('/api/github-repos');
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    allRepos = data;
    populateLangFilter();
    renderProjects();
  } catch {
    document.getElementById('projectsGrid').innerHTML =
      `<p class="projects-loading">Could not load projects. <a href="https://github.com/Srijan1105" target="_blank" style="color:var(--accent-light)">View on GitHub →</a></p>`;
  }
}

document.querySelectorAll('.filter-pill').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.filter;
    renderProjects();
  });
});

const searchEl = document.getElementById('projectSearch');
const clearBtn = document.getElementById('clearSearch');
searchEl?.addEventListener('input', () => { clearBtn.style.display = searchEl.value ? 'block' : 'none'; renderProjects(); });
clearBtn?.addEventListener('click', () => { searchEl.value = ''; clearBtn.style.display = 'none'; renderProjects(); });
document.getElementById('langFilter')?.addEventListener('change', renderProjects);
document.getElementById('sortFilter')?.addEventListener('change', renderProjects);

loadProjects();
