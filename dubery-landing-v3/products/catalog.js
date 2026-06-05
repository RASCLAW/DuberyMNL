/* products/catalog.js — render 11-card grid + series filter + deep-linkable ?series= */
'use strict';

(async function () {
  const grid = document.querySelector('[data-catalog-grid]');
  if (!grid) return;

  const res = await fetch('data.json');
  const items = await res.json();

  // Render cards
  function starsFromRating(r) {
    const full = Math.round(r);
    return '★★★★★'.slice(0, full) + '☆☆☆☆☆'.slice(0, 5 - full);
  }

  function renderCard(p) {
    const href = `item.html?slug=${encodeURIComponent(p.slug)}`;
    const imgs = (Array.isArray(p.cardImages) && p.cardImages.length) ? p.cardImages : [p.hero, p.hover];
    const imgTags = imgs.map((src, i) =>
      `<img class="bs-img${i === 0 ? ' is-active' : ''}" src="${src}" alt="${i === 0 ? `${p.name} ${p.colorway}` : ''}" loading="lazy">`
    ).join('');
    const dotTags = imgs.map((_, i) => `<span class="bs-dot${i === 0 ? ' active' : ''}"></span>`).join('');
    return `
      <a href="${href}" class="bs-card catalog-card" data-series="${p.series}">
        <div class="bs-media">
          ${imgTags}
          <div class="bs-nav-bar">
            <button class="bs-nav bs-nav--prev" aria-label="Previous">&#8249;</button>
            <button class="bs-nav bs-nav--next" aria-label="Next">&#8250;</button>
          </div>
        </div>
        <div class="bs-dots">${dotTags}</div>
        <div class="bs-meta">
          <div class="bs-rating">
            <span class="bs-stars" aria-label="${p.rating} stars">${starsFromRating(p.rating)}</span>
            <span class="bs-count">(${p.count})</span>
          </div>
          <h3 class="bs-title">${p.seriesLabel} ${p.colorLabel} <span class="bs-colorway">| ${p.colorway}</span></h3>
          <div class="bs-price">₱${p.price}</div>
        </div>
      </a>
    `;
  }

  grid.innerHTML = items.map(renderCard).join('');

  // Swipe + arrow navigation on cards (N-image carousel, wraps around)
  function attachCardSwipe(cards) {
    cards.forEach(card => {
      const imgs = card.querySelectorAll('.bs-img');
      const dots = card.querySelectorAll('.bs-dot');
      const n = imgs.length;
      if (n <= 1) return;
      let idx = 0;

      function show(i) {
        idx = (i + n) % n;
        imgs.forEach((im, k) => im.classList.toggle('is-active', k === idx));
        dots.forEach((d, k) => d.classList.toggle('active', k === idx));
      }

      card.querySelectorAll('.bs-nav').forEach(btn => {
        btn.addEventListener('click', e => {
          e.preventDefault();
          e.stopPropagation();
          show(idx + (btn.classList.contains('bs-nav--next') ? 1 : -1));
        });
      });

      // Tapping a pagination dot jumps to that image (don't follow the card link)
      dots.forEach((dot, k) => {
        dot.addEventListener('click', e => {
          e.preventDefault();
          e.stopPropagation();
          show(k);
        });
      });

      let startX = 0;
      card.addEventListener('touchstart', e => {
        startX = e.touches[0].clientX;
      }, { passive: true });
      card.addEventListener('touchend', e => {
        const dx = e.changedTouches[0].clientX - startX;
        if (Math.abs(dx) > 40) {
          e.preventDefault();
          show(idx + (dx < 0 ? 1 : -1));
        }
      });
    });
  }
  attachCardSwipe(grid.querySelectorAll('.catalog-card'));

  // Update counts in filter pills
  const counts = { all: items.length };
  items.forEach(p => { counts[p.series] = (counts[p.series] || 0) + 1; });
  document.querySelectorAll('.filter-count').forEach(el => {
    const key = el.dataset.count;
    if (counts[key]) el.textContent = `(${counts[key]})`;
  });

  // Filter logic
  const cards = grid.querySelectorAll('.catalog-card');
  function applyFilter(filter) {
    cards.forEach(card => {
      const match = filter === 'all' || card.dataset.series === filter;
      card.hidden = !match;
    });
    document.querySelectorAll('.bs-filter').forEach(p => {
      p.classList.toggle('is-active', p.dataset.filter === filter);
    });
  }

  document.querySelectorAll('.bs-filter').forEach(pill => {
    pill.addEventListener('click', () => {
      const filter = pill.dataset.filter;
      applyFilter(filter);
      const url = new URL(location.href);
      if (filter === 'all') url.searchParams.delete('series');
      else url.searchParams.set('series', filter);
      history.replaceState(null, '', url);
    });
  });

  // Honor ?series= on load
  const initial = new URLSearchParams(location.search).get('series');
  if (initial && counts[initial]) applyFilter(initial);
})();
