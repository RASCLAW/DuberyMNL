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
    return `
      <a href="${href}" class="bs-card catalog-card" data-series="${p.series}">
        <div class="bs-media">
          <img class="bs-img primary" src="${p.hero}" alt="${p.name} ${p.colorway}" loading="lazy">
          <img class="bs-img hover" src="${p.hover}" alt="" loading="lazy">
        </div>
        <div class="bs-meta">
          <div class="bs-rating">
            <span class="bs-stars" aria-label="${p.rating} stars">${starsFromRating(p.rating)}</span>
            <span class="bs-count">(${p.count})</span>
          </div>
          <h3 class="bs-title">${p.name.toUpperCase()} <span class="bs-colorway">| ${p.colorway}</span></h3>
          <div class="bs-price">₱${p.price}</div>
          <div class="bs-swatches">
            <span class="bs-swatch is-active" style="background:${p.swatch}"></span>
          </div>
        </div>
      </a>
    `;
  }

  grid.innerHTML = items.map(renderCard).join('');

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
