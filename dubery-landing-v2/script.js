/* DuberyMNL v2 — simple scroll
   Lenis smooth · peacock tile-floor scroll-linked · progress bar · stat counters
   No section visibility animation. Sections are always visible (normal flow). */

(() => {
  'use strict';

  // ── Populate tile-floor (131 UGC tiles on desktop, 66 on mobile, doubled for seamless loop) ──
  // Eager load + async decode: tiles are ~25KB each, and lazy-loading causes decode jitter
  // mid-scroll as the GSAP scrub reveals new rows inside the 3D-transformed parent.
  const floor = document.getElementById('tileFloor');
  if (floor) {
    const isMobileViewport = window.matchMedia('(max-width: 768px)').matches;
    const count = isMobileViewport ? 66 : 131;
    const imgs = [];
    for (let pass = 0; pass < 2; pass++) {
      for (let i = 1; i <= count; i++) {
        const n = String(i).padStart(3, '0');
        imgs.push(`<img src="assets/tile-mix/tile-${n}.jpg" decoding="async" alt="">`);
      }
    }
    floor.innerHTML = imgs.join('');
  }

  // ── Lenis smooth scroll ──
  let lenis = null;
  if (window.Lenis) {
    lenis = new Lenis({
      duration: 1.1,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });
    const raf = (time) => { lenis.raf(time); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
  }

  // Peacock tile-floor stays static. Previous design used a GSAP scrub
  // (yPercent: -50 tied to body scroll) but combined with the 3D-rotated parent
  // + 262 tile imgs + mask-image, it forced whole-layer recomposite on every
  // scroll frame and dropped scrolling to ~8fps. The fixed-bg vignette gives the
  // illusion of depth without the per-frame GPU cost.

  // ── Anchor click smooth-scroll via Lenis ──
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href').slice(1);
      if (!id) return;
      const target = document.getElementById(id);
      if (!target) return;
      e.preventDefault();
      if (lenis) lenis.scrollTo(target, { offset: -20, duration: 1.2 });
      else target.scrollIntoView({ behavior: 'smooth' });
    });
  });

  // ── Progress bar (idempotent) ──
  const bar = document.querySelector('[data-progress-bar]');
  let lastBarP = -1;
  const updateBar = () => {
    if (!bar) return;
    const h = document.documentElement.scrollHeight - window.innerHeight;
    const p = h > 0 ? window.scrollY / h : 0;
    if (Math.abs(p - lastBarP) < 0.001) return;
    lastBarP = p;
    bar.style.transform = `scaleX(${p})`;
  };
  if (bar) updateBar();

  // ── Stat counters (animate once when scrolled into view) ──
  const counters = document.querySelectorAll('.stat-number');
  if (counters.length && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = parseFloat(el.dataset.value);
        const decimals = parseInt(el.dataset.decimals || '0', 10);
        const duration = 1500;
        const start = performance.now();
        const step = (now) => {
          const t = Math.min(1, (now - start) / duration);
          const eased = 1 - Math.pow(1 - t, 3);
          const v = eased * target;
          el.textContent = decimals > 0 ? v.toFixed(decimals) : Math.round(v);
          if (t < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
        io.unobserve(el);
      });
    }, { threshold: 0.3 });
    counters.forEach((c) => io.observe(c));
  }

  // ── Auto-hide header on scroll down (idempotent) ──
  const header = document.querySelector('.site-header');
  let lastY = 0;
  let headerHidden = false;
  const updateHeader = () => {
    if (!header) return;
    const y = window.scrollY;
    const shouldHide = (y > lastY && y > 80);
    if (shouldHide !== headerHidden) {
      headerHidden = shouldHide;
      header.style.transform = shouldHide ? 'translateY(-100%)' : 'translateY(0)';
    }
    lastY = y;
  };

  // ── Section fade + peacock dim overlay (desktop only; mobile keeps sections solid) ──
  const isMobile = window.matchMedia('(max-width: 768px)').matches;
  const fadeSections = document.querySelectorAll('.flow-section');
  const darkOverlay = document.getElementById('dark-overlay');
  const OVERLAY_MAX = 0.62;
  const fadeZone = 0.22;
  let lastOverlayOpacity = -1;
  const sectionState = new WeakMap();

  const quantize = (v) => Math.round(v * 1000) / 1000;
  const setSectionOpacity = (sec, opacity) => {
    const q = quantize(opacity);
    if (sectionState.get(sec) === q) return;
    sectionState.set(sec, q);
    sec.style.opacity = q;
  };
  const setOverlayOpacity = (opacity) => {
    if (!darkOverlay) return;
    const q = quantize(opacity);
    if (q === lastOverlayOpacity) return;
    lastOverlayOpacity = q;
    darkOverlay.style.opacity = q;
  };

  const updateFade = () => {
    const vh = window.innerHeight;
    const zone = vh * fadeZone;
    let maxOpacity = 0;
    fadeSections.forEach(sec => {
      const { top } = sec.getBoundingClientRect();
      let opacity;
      if (top >= vh) {
        opacity = 0;
      } else if (top > vh - zone) {
        opacity = (vh - top) / zone;
      } else {
        opacity = 1;
      }
      opacity = Math.max(0, Math.min(1, opacity));
      setSectionOpacity(sec, opacity);
      if (opacity > maxOpacity) maxOpacity = opacity;
    });
    setOverlayOpacity(maxOpacity * OVERLAY_MAX);
  };

  if (isMobile) {
    fadeSections.forEach(sec => { sec.style.opacity = 1; });
    if (darkOverlay) darkOverlay.style.opacity = OVERLAY_MAX;
  }

  // ── Single rAF-throttled scroll tick: bar + header + fade ──
  let rafPending = false;
  const tick = () => {
    updateBar();
    updateHeader();
    if (!isMobile) updateFade();
    rafPending = false;
  };
  const onScroll = () => {
    if (!rafPending) { rafPending = true; requestAnimationFrame(tick); }
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  tick();
  // ── Lightning effect around hero title ──
  const canvas = document.getElementById('lightning-canvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let w, h;

    const resize = () => {
      const rect = canvas.parentElement.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      const pad = 30;
      w = canvas.width = (rect.width + pad * 2) * dpr;
      h = canvas.height = (rect.height + pad * 2) * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener('resize', resize);

    // Recursive lightning bolt
    const bolt = (x1, y1, x2, y2, depth) => {
      if (depth === 0) { ctx.lineTo(x2, y2); return; }
      const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
      const dx = x2 - x1, dy = y2 - y1;
      const len = Math.sqrt(dx * dx + dy * dy);
      const offset = (Math.random() - 0.5) * len * 0.4;
      const px = mx - dy / len * offset;
      const py = my + dx / len * offset;
      bolt(x1, y1, px, py, depth - 1);
      bolt(px, py, x2, y2, depth - 1);
      if (depth > 2 && Math.random() < 0.25) {
        const fLen = len * 0.25;
        const ang = Math.atan2(y2 - y1, x2 - x1) + (Math.random() - 0.5) * 1.2;
        ctx.moveTo(px, py);
        bolt(px, py, px + Math.cos(ang) * fLen, py + Math.sin(ang) * fLen, depth - 2);
      }
    };

    // Edge point hugging the text bounding box
    const edgePoint = (cw, ch) => {
      const pad = 8;
      const side = Math.floor(Math.random() * 4);
      switch (side) {
        case 0: return { x: pad + Math.random() * (cw - pad * 2), y: pad };
        case 1: return { x: cw - pad, y: pad + Math.random() * (ch - pad * 2) };
        case 2: return { x: pad + Math.random() * (cw - pad * 2), y: ch - pad };
        case 3: return { x: pad, y: pad + Math.random() * (ch - pad * 2) };
      }
    };

    let activeBolts = [];
    let drawing = false;
    let nextBoltTimer = null;

    const scheduleNext = () => {
      const gap = 8000 + Math.random() * 37000; // 8-45s
      nextBoltTimer = setTimeout(() => {
        const cw = w / (window.devicePixelRatio || 1);
        const ch = h / (window.devicePixelRatio || 1);
        spawnBurst(cw, ch);
        startDrawing();
        scheduleNext();
      }, gap);
    };
    const startDrawing = () => {
      if (drawing) return;
      drawing = true;
      requestAnimationFrame(draw);
    };

    const spawnBurst = (cw, ch) => {
      // 1-3 bolts in a quick burst
      const count = 1 + Math.floor(Math.random() * 3);
      for (let i = 0; i < count; i++) {
        const a = edgePoint(cw, ch);
        const b = edgePoint(cw, ch);
        const dist = Math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2);
        if (dist < 40) continue;
        activeBolts.push({
          x1: a.x, y1: a.y, x2: b.x, y2: b.y,
          life: 1,
          decay: 0.02 + Math.random() * 0.015,
          width: 1 + Math.random() * 1.5,
          delay: i * (30 + Math.random() * 60), // stagger within burst
          born: performance.now(),
        });
      }
    };

    const draw = () => {
      const cw = w / (window.devicePixelRatio || 1);
      const ch = h / (window.devicePixelRatio || 1);
      ctx.clearRect(0, 0, cw, ch);
      const now = performance.now();

      for (let i = activeBolts.length - 1; i >= 0; i--) {
        const b = activeBolts[i];
        if (now - b.born < b.delay) continue; // wait for stagger
        b.life -= b.decay;
        if (b.life <= 0) { activeBolts.splice(i, 1); continue; }

        const alpha = b.life;

        // Glow
        ctx.beginPath();
        ctx.moveTo(b.x1, b.y1);
        bolt(b.x1, b.y1, b.x2, b.y2, 5);
        ctx.strokeStyle = `rgba(232, 17, 15, ${alpha * 0.35})`;
        ctx.lineWidth = b.width + 4;
        ctx.shadowColor = '#E8110F';
        ctx.shadowBlur = 18;
        ctx.stroke();

        // Core
        ctx.beginPath();
        ctx.moveTo(b.x1, b.y1);
        bolt(b.x1, b.y1, b.x2, b.y2, 5);
        ctx.strokeStyle = `rgba(255, 230, 230, ${alpha * 0.85})`;
        ctx.lineWidth = b.width;
        ctx.shadowBlur = 6;
        ctx.shadowColor = '#ff4444';
        ctx.stroke();

        ctx.shadowBlur = 0;
      }

      if (activeBolts.length > 0) {
        requestAnimationFrame(draw);
      } else {
        drawing = false;
      }
    };
    scheduleNext();
  }
})();
