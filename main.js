// Typing animation
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
      reqSuccess.textContent = data.message;
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

// ── View Counter (SSE) ────────────────────────────────────────────────────────
(function () {
  // Track this visit
  fetch('/api/views/track', { method: 'POST' }).catch(() => {});

  const el = document.getElementById('viewCount');

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

  let lastCount = 0;

  if (typeof EventSource !== 'undefined') {
    const es = new EventSource('/api/views/stream');
    es.onmessage = (e) => {
      const count = parseInt(e.data, 10);
      if (!isNaN(count)) {
        animateCount(lastCount, count);
        lastCount = count;
      }
    };
    es.onerror = () => {
      // Fallback to polling if SSE fails
      es.close();
      startPolling();
    };
  } else {
    startPolling();
  }

  function startPolling() {
    async function poll() {
      try {
        const res = await fetch('/api/views/track', { method: 'POST' });
        const data = await res.json();
        animateCount(lastCount, data.total);
        lastCount = data.total;
      } catch {}
    }
    setInterval(poll, 10000);
  }
})();
