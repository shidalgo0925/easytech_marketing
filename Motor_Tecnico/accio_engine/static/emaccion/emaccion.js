(function () {
  'use strict';

  const navToggle = document.getElementById('lpMenuToggle');
  const mobileMenu = document.getElementById('lpMobileMenu');
  if (navToggle && mobileMenu) {
    navToggle.addEventListener('click', () => {
      const open = mobileMenu.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    mobileMenu.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', () => mobileMenu.classList.remove('is-open'));
    });
  }

  document.querySelectorAll('.lp-faq-q').forEach((btn) => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.lp-faq-item');
      const wasOpen = item.classList.contains('is-open');
      document.querySelectorAll('.lp-faq-item').forEach((i) => i.classList.remove('is-open'));
      if (!wasOpen) item.classList.add('is-open');
      btn.setAttribute('aria-expanded', !wasOpen ? 'true' : 'false');
    });
  });

  const revealEls = document.querySelectorAll('.lp-reveal');
  if ('IntersectionObserver' in window && revealEls.length) {
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add('is-visible');
            obs.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    revealEls.forEach((el) => obs.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add('is-visible'));
  }

  const form = document.getElementById('lpLeadForm');
  const msg = document.getElementById('lpFormMsg');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (msg) {
        msg.className = 'lp-form-msg';
        msg.textContent = '';
      }
      const btn = form.querySelector('[type=submit]');
      if (btn) btn.disabled = true;
      try {
        const r = await fetch('/accio/producto/lead', {
          method: 'POST',
          body: new FormData(form),
        });
        const j = await r.json();
        if (msg) {
          msg.className = 'lp-form-msg ' + (j.ok ? 'is-ok' : 'is-err');
          msg.textContent = j.ok
            ? (j.message || 'Solicitud recibida. Le contactaremos pronto.')
            : (j.error || 'Error al enviar. Intente de nuevo.');
        }
        if (j.ok) form.reset();
      } catch {
        if (msg) {
          msg.className = 'lp-form-msg is-err';
          msg.textContent = 'Error de conexión. Escríbanos por WhatsApp.';
        }
      } finally {
        if (btn) btn.disabled = false;
      }
    });
  }

  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (!id || id === '#') return;
      const target = document.querySelector(id);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  const demoPlayer = document.getElementById('lpDemoPlayer');
  const demoPlay = document.getElementById('lpDemoPlay');
  const demoStop = document.getElementById('lpDemoStop');
  const demoStage = document.getElementById('lpDemoStage');
  const demoPoster = document.getElementById('lpDemoPoster');
  const demoProgress = document.getElementById('lpDemoProgress');
  const demoProgressBar = document.getElementById('lpDemoProgressBar');
  let demoTimer = null;
  let demoIndex = 0;

  function showDemoSlide(index) {
    if (!demoStage) return;
    const slides = demoStage.querySelectorAll('.lp-demo-slide');
    slides.forEach((slide, i) => {
      const active = i === index;
      slide.classList.toggle('is-active', active);
      slide.hidden = !active;
    });
    if (demoProgress && demoProgressBar) {
      const pct = Math.round(((index + 1) / slides.length) * 100);
      demoProgress.setAttribute('aria-valuenow', String(pct));
      demoProgressBar.style.width = pct + '%';
    }
  }

  function stopDemo() {
    if (demoTimer) {
      clearInterval(demoTimer);
      demoTimer = null;
    }
    demoIndex = 0;
    if (demoPlayer) demoPlayer.classList.remove('is-playing');
    if (demoStage) demoStage.hidden = true;
    if (demoPoster) demoPoster.hidden = false;
    if (demoStop) demoStop.hidden = true;
    if (demoProgressBar) demoProgressBar.style.width = '0%';
    if (demoProgress) demoProgress.setAttribute('aria-valuenow', '0');
  }

  function startDemo() {
    if (!demoPlayer || !demoStage) return;
    demoPlayer.classList.add('is-playing');
    demoStage.hidden = false;
    if (demoPoster) demoPoster.hidden = true;
    if (demoStop) demoStop.hidden = false;
    demoIndex = 0;
    showDemoSlide(demoIndex);
    demoTimer = setInterval(() => {
      demoIndex += 1;
      const total = demoStage.querySelectorAll('.lp-demo-slide').length;
      if (demoIndex >= total) {
        stopDemo();
        return;
      }
      showDemoSlide(demoIndex);
    }, 4500);
  }

  if (demoPlay) demoPlay.addEventListener('click', startDemo);
  if (demoPoster) demoPoster.addEventListener('click', startDemo);
  if (demoStop) demoStop.addEventListener('click', stopDemo);
})();
