/* shop-social/shop-social.js — render UGC wall + lightbox with tagged products */
'use strict';

(async function () {
  const wall = document.querySelector('[data-social-wall]');
  const lb = document.querySelector('[data-lightbox]');
  if (!wall || !lb) return;

  const [tiles, products] = await Promise.all([
    fetch('data.json').then(r => r.json()),
    fetch('../products/data.json').then(r => r.json()),
  ]);
  const productBySlug = Object.fromEntries(products.map(p => [p.slug, p]));

  const PAGE_INIT = 24;
  const PAGE_INC  = 12;
  let loaded = 0;

  // Load More button — appended inside .container so it inherits width/centering
  const loadMoreWrap = document.createElement('div');
  loadMoreWrap.className = 'load-more-wrap';
  const loadMoreBtn = document.createElement('button');
  loadMoreBtn.type = 'button';
  loadMoreBtn.className = 'btn btn-ghost load-more-btn';
  loadMoreBtn.textContent = 'Load more';
  loadMoreWrap.appendChild(loadMoreBtn);
  wall.insertAdjacentElement('afterend', loadMoreWrap);

  function renderTile(t) {
    const tagLabels = t.products
      .map(slug => productBySlug[slug])
      .filter(Boolean)
      .slice(0, 2)
      .map(p => `<span class="social-tag-dot" style="background:${p.swatch}"></span>`)
      .join('');
    return `
      <button type="button" id="tile-${t.id}" class="social-tile wall-tile" data-tile="${t.id}" aria-label="Shop this look by ${t.author}">
        <img src="${t.image}" alt="${t.caption}" loading="lazy">
        <span class="social-tag"><span class="tag-dots">${tagLabels}</span><span class="tag-label">Shop this look</span></span>
      </button>
    `;
  }

  function appendTiles(from, to) {
    // Anchor scroll to the load-more button so column reflow doesn't jump the page
    const anchorY = loadMoreWrap.getBoundingClientRect().top + window.scrollY;

    const batch = tiles.slice(from, to);
    batch.forEach(t => {
      wall.insertAdjacentHTML('beforeend', renderTile(t));
      const btn = wall.querySelector(`#tile-${t.id}`);
      btn.addEventListener('click', () => {
        const idx = tiles.findIndex(x => x.id === t.id);
        openTile(idx);
      });
    });
    loaded = Math.min(to, tiles.length);
    loadMoreWrap.hidden = loaded >= tiles.length;

    // Restore scroll so the button stays in the same viewport position
    const newAnchorY = loadMoreWrap.getBoundingClientRect().top + window.scrollY;
    window.scrollBy(0, newAnchorY - anchorY);
  }

  // Initial load
  appendTiles(0, PAGE_INIT);

  loadMoreBtn.addEventListener('click', () => {
    appendTiles(loaded, loaded + PAGE_INC);
  });

  // Lightbox elements
  const lbImg      = lb.querySelector('[data-lightbox-image]');
  const lbAuthor   = lb.querySelector('[data-lightbox-author]');
  const lbLocation = lb.querySelector('[data-lightbox-location]');
  const lbCaption  = lb.querySelector('[data-lightbox-caption]');
  const lbProducts = lb.querySelector('[data-lightbox-products]');
  const btnPrev    = lb.querySelector('[data-lightbox-prev]');
  const btnNext    = lb.querySelector('[data-lightbox-next]');
  const btnClose   = lb.querySelector('[data-lightbox-close]');

  let currentIdx = -1;

  function productCard(p) {
    return `
      <a class="lightbox-product" href="../products/item.html?slug=${p.slug}">
        <div class="lightbox-product-media"><img src="${p.thumb}" alt="${p.name} ${p.colorway}"></div>
        <div class="lightbox-product-meta">
          <div class="lightbox-product-series">${p.seriesLabel}</div>
          <div class="lightbox-product-name">${p.name} <span>${p.colorway}</span></div>
          <div class="lightbox-product-price">₱${p.price}</div>
        </div>
        <span class="lightbox-product-cta">Shop →</span>
      </a>
    `;
  }

  function openTile(idx) {
    const t = tiles[idx];
    if (!t) return;
    currentIdx = idx;
    lbImg.src = t.image;
    lbImg.alt = t.caption;
    lbAuthor.textContent = t.author;
    lbLocation.textContent = t.location;
    lbCaption.textContent = t.caption;
    lbProducts.innerHTML = t.products
      .map(slug => productBySlug[slug])
      .filter(Boolean)
      .map(productCard)
      .join('');
    lb.hidden = false;
    document.body.style.overflow = 'hidden';
    history.replaceState(null, '', `#tile-${t.id}`);
    btnClose.focus();
  }

  function closeLightbox() {
    lb.hidden = true;
    document.body.style.overflow = '';
    history.replaceState(null, '', location.pathname);
    currentIdx = -1;
  }

  function step(dir) {
    if (currentIdx < 0) return;
    const next = (currentIdx + dir + tiles.length) % tiles.length;
    // Auto-load if stepping into unloaded territory
    if (next >= loaded) appendTiles(loaded, next + 1);
    openTile(next);
  }

  btnClose.addEventListener('click', closeLightbox);
  btnPrev.addEventListener('click', () => step(-1));
  btnNext.addEventListener('click', () => step(1));
  lb.addEventListener('click', (e) => { if (e.target === lb) closeLightbox(); });
  document.addEventListener('keydown', (e) => {
    if (lb.hidden) return;
    if (e.key === 'Escape') closeLightbox();
    else if (e.key === 'ArrowLeft') step(-1);
    else if (e.key === 'ArrowRight') step(1);
  });

  // Deep-link #tile-N on load
  const hash = location.hash.match(/^#tile-(\d+)$/);
  if (hash) {
    const id = +hash[1];
    const idx = tiles.findIndex(x => x.id === id);
    if (idx >= 0) {
      if (idx >= loaded) appendTiles(loaded, idx + 1);
      openTile(idx);
    }
  }
})();
