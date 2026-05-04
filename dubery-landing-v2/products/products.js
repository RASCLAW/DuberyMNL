/* DuberyMNL — Products page
   Populates tile-floor, handles filter tabs + URL ?series= param */

(() => {
  'use strict';

  // ── Populate peacock tile-floor (same source as home) ──
  const floor = document.getElementById('productsTileFloor');
  if (floor) {
    const count = 131;
    const imgs = [];
    for (let pass = 0; pass < 2; pass++) {
      for (let i = 1; i <= count; i++) {
        const n = String(i).padStart(3, '0');
        imgs.push(`<img src="../assets/tile-mix/tile-${n}.jpg" loading="lazy" alt="">`);
      }
    }
    floor.innerHTML = imgs.join('');
  }

  // ── Filter tabs ─────────────────────────────────────────
  const tabs = document.querySelectorAll('.filter-tab');
  const tiles = document.querySelectorAll('.product-tile');

  function applyFilter(series) {
    tiles.forEach(t => {
      const s = t.dataset.series;
      t.style.display = (series === 'all' || s === series) ? '' : 'none';
    });
    tabs.forEach(t => {
      t.classList.toggle('is-active', t.dataset.filter === series);
    });
  }

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const s = tab.dataset.filter;
      applyFilter(s);
      const url = new URL(window.location.href);
      if (s === 'all') url.searchParams.delete('series');
      else url.searchParams.set('series', s);
      history.replaceState(null, '', url);
    });
  });

  // Read URL ?series=
  const params = new URLSearchParams(window.location.search);
  const initial = params.get('series');
  if (initial && ['bandits','outback','rasta'].includes(initial)) {
    applyFilter(initial);
  }

  // ── Progress bar ─────────────────────────────────────────
  const bar = document.querySelector('[data-progress-bar]');
  if (bar) {
    const onScroll = () => {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      const p = h > 0 ? window.scrollY / h : 0;
      bar.style.transform = `scaleX(${p})`;
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }
})();
