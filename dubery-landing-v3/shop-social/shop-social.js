/* shop-social/shop-social.js — UGC wall + lightbox + ?edit mode */
'use strict';

(async function () {
  const wall = document.querySelector('[data-social-wall]');
  const lb   = document.querySelector('[data-lightbox]');
  if (!wall || !lb) return;

  const isEdit = new URLSearchParams(location.search).has('edit');

  const [tilesRaw, products] = await Promise.all([
    fetch('data.json?v=v3-013').then(r => r.json()),
    fetch('../products/data.json?v=v3-013').then(r => r.json()),
  ]);

  // Deep-copy so edits don't mutate the original
  let data = tilesRaw.map(t => ({ ...t, products: [...t.products] }));

  const productBySlug = Object.fromEntries(products.map(p => [p.slug, p]));

  // ── Render wall ────────────────────────────────────────────────────────────

  function tagDots(slugs) {
    return slugs
      .map(s => productBySlug[s])
      .filter(Boolean)
      .slice(0, 2)
      .map(p => `<span class="social-tag-dot" style="background:${p.swatch}"></span>`)
      .join('');
  }

  function renderAll() {
    wall.innerHTML = data.map(t => `
      <button type="button" id="tile-${t.id}" class="social-tile wall-tile" data-tile="${t.id}" aria-label="Shop this look by ${t.author}">
        <img src="${t.image}" alt="${t.caption}" loading="lazy">
        ${isEdit ? `<span role="button" tabindex="0" class="tile-remove-btn" data-remove="${t.id}" aria-label="Remove tile">✕</span>` : ''}
        <span class="social-tag"><span class="tag-dots">${tagDots(t.products)}</span><span class="tag-label">Shop this look</span></span>
      </button>
    `).join('');

    wall.querySelectorAll('[data-tile]').forEach(btn => {
      btn.addEventListener('click', e => {
        if (e.target.closest('[data-remove]')) return;
        const idx = data.findIndex(x => x.id === +btn.dataset.tile);
        if (isEdit) openEditor(idx);
        else openLightbox(idx);
      });
    });

    if (isEdit) {
      wall.querySelectorAll('[data-remove]').forEach(btn => {
        const remove = e => {
          e.stopPropagation();
          data = data.filter(t => t.id !== +btn.dataset.remove);
          renderAll();
        };
        btn.addEventListener('click', remove);
        btn.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') remove(e); });
      });
    }
  }

  renderAll();

  // ── Edit bar ───────────────────────────────────────────────────────────────

  if (isEdit) {
    const bar = document.createElement('div');
    bar.className = 'ss-edit-bar';
    bar.innerHTML = `
      <span class="ss-edit-bar-label">Edit Mode</span>
      <button type="button" class="btn btn-primary ss-export-btn">Download data.json</button>
      <a href="?" class="btn btn-ghost">Exit Edit</a>
    `;
    document.body.appendChild(bar);

    bar.querySelector('.ss-export-btn').addEventListener('click', () => {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'data.json';
      a.click();
    });
  }

  // ── Edit panel ─────────────────────────────────────────────────────────────

  const editPanel = document.createElement('div');
  editPanel.className = 'ss-edit-panel';
  editPanel.hidden = true;
  editPanel.innerHTML = `
    <div class="ss-edit-panel-inner">
      <div class="ss-edit-panel-head">
        <h3>Edit tile</h3>
        <button type="button" class="ss-edit-panel-close" aria-label="Close">✕</button>
      </div>
      <label class="ss-field">Author
        <input type="text" id="ep-author" placeholder="@handle">
      </label>
      <label class="ss-field">Location
        <input type="text" id="ep-location" placeholder="City / Place">
      </label>
      <label class="ss-field">Caption
        <textarea id="ep-caption" rows="3" placeholder="Caption text"></textarea>
      </label>
      <div class="ss-field">
        <span class="ss-field-label">Products tagged</span>
        <div id="ep-products" class="ep-chips"></div>
      </div>
      <button type="button" class="btn btn-primary ss-save-btn">Save</button>
    </div>
  `;
  document.body.appendChild(editPanel);

  let editingIdx = -1;

  function openEditor(idx) {
    const t = data[idx];
    editingIdx = idx;

    editPanel.querySelector('#ep-author').value   = t.author;
    editPanel.querySelector('#ep-location').value = t.location;
    editPanel.querySelector('#ep-caption').value  = t.caption;

    const chips = editPanel.querySelector('#ep-products');
    chips.innerHTML = products.map(p => `
      <label class="ep-chip${t.products.includes(p.slug) ? ' active' : ''}">
        <input type="checkbox" value="${p.slug}" ${t.products.includes(p.slug) ? 'checked' : ''}>
        <span class="ep-chip-dot" style="background:${p.swatch}"></span>
        ${p.name} ${p.colorLabel || p.colorway}
      </label>
    `).join('');

    chips.querySelectorAll('input[type="checkbox"]').forEach(cb => {
      cb.addEventListener('change', () => cb.closest('.ep-chip').classList.toggle('active', cb.checked));
    });

    editPanel.hidden = false;
    document.body.style.overflow = 'hidden';
  }

  editPanel.querySelector('.ss-edit-panel-close').addEventListener('click', () => {
    editPanel.hidden = true;
    document.body.style.overflow = '';
    editingIdx = -1;
  });

  editPanel.querySelector('.ss-save-btn').addEventListener('click', () => {
    if (editingIdx < 0) return;
    const t = data[editingIdx];
    t.author   = editPanel.querySelector('#ep-author').value.trim();
    t.location = editPanel.querySelector('#ep-location').value.trim();
    t.caption  = editPanel.querySelector('#ep-caption').value.trim();
    t.products = [...editPanel.querySelectorAll('#ep-products input:checked')].map(cb => cb.value);
    editPanel.hidden = true;
    document.body.style.overflow = '';
    editingIdx = -1;
    renderAll();
  });

  editPanel.addEventListener('click', e => { if (e.target === editPanel) {
    editPanel.hidden = true; document.body.style.overflow = ''; editingIdx = -1;
  }});

  // ── Lightbox (normal mode only) ────────────────────────────────────────────

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
          <div class="lightbox-product-name">${p.name} <span>${p.colorLabel || p.colorway}</span></div>
          <div class="lightbox-product-price">₱${p.price}</div>
        </div>
        <span class="lightbox-product-cta">Shop →</span>
      </a>
    `;
  }

  function openLightbox(idx) {
    const t = data[idx];
    if (!t) return;
    currentIdx = idx;
    lbImg.src = t.image;
    lbImg.alt = t.caption;
    lbAuthor.textContent   = t.author;
    lbLocation.textContent = t.location;
    lbCaption.textContent  = t.caption;
    lbProducts.innerHTML   = t.products
      .map(s => productBySlug[s]).filter(Boolean).map(productCard).join('');
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
    openLightbox((currentIdx + dir + data.length) % data.length);
  }

  if (!isEdit) {
    btnClose.addEventListener('click', closeLightbox);
    btnPrev.addEventListener('click', () => step(-1));
    btnNext.addEventListener('click', () => step(1));
    lb.addEventListener('click', e => { if (e.target === lb) closeLightbox(); });
    document.addEventListener('keydown', e => {
      if (lb.hidden) return;
      if (e.key === 'Escape') closeLightbox();
      else if (e.key === 'ArrowLeft') step(-1);
      else if (e.key === 'ArrowRight') step(1);
    });

    // Deep-link #tile-N on load
    const hash = location.hash.match(/^#tile-(\d+)$/);
    if (hash) {
      const idx = data.findIndex(x => x.id === +hash[1]);
      if (idx >= 0) openLightbox(idx);
    }
  }
})();
