/* Image Bank tab */
(function () {
  let allImages = [];
  let filtered = [];
  let activeType = 'all';
  let activeModel = 'all';
  let lbIndex = 0;
  // Favorites store: server-side at /api/schedule/favorites (shared with the
  // Schedule picker so both surfaces show the same hearts). Keys are project-
  // relative PATHS like "contents/ready/.../foo.png". The in-memory Set holds
  // URLs (/api/images/contents/...) for easier render-time matching against
  // `img.url`. URL <-> path conversion is one line.
  let favorites = new Set();

  // Ad-hoc multi-select store: in-memory Set of image URLs (/api/images/...).
  // Independent of favorites -- ephemeral, cleared on "Clear" or page reload.
  // Selection mode is "on" whenever selected.size > 0 (Google-Photos style:
  // once anything is selected, a plain thumb click toggles selection instead
  // of opening the lightbox).
  let selected = new Set();

  const grid       = document.getElementById('ib-grid');
  const loading    = document.getElementById('ib-loading');
  const count      = document.getElementById('ib-count');
  const search     = document.getElementById('ib-search');
  const typeGrp    = document.getElementById('ib-type-filters');
  const modelGrp   = document.getElementById('ib-model-filters');
  const lb         = document.getElementById('ib-lightbox');
  const lbImg      = document.getElementById('ib-lb-img');
  const lbType     = document.getElementById('ib-lb-type');
  const lbModel    = document.getElementById('ib-lb-model');
  const lbName     = document.getElementById('ib-lb-name');
  const lbDl       = document.getElementById('ib-lb-dl');
  const lbCopy     = document.getElementById('ib-lb-copy');
  const lbArchive  = document.getElementById('ib-lb-archive') || document.createElement('button');
  const lbFav      = document.getElementById('ib-lb-fav') || document.createElement('button');
  const lbClose    = document.getElementById('ib-lb-close');
  const lbPrev     = document.getElementById('ib-lb-prev');
  const lbNext     = document.getElementById('ib-lb-next');
  const lbBack     = document.getElementById('ib-lb-backdrop');
  const copyPaths  = document.getElementById('ib-copy-paths') || document.createElement('button');
  const refreshBtn = document.getElementById('ib-refresh');
  const selBar     = document.getElementById('ib-selbar');
  const selCount   = document.getElementById('ib-selbar-count');
  const selCopy    = document.getElementById('ib-sel-copy');
  const selCopyUrl = document.getElementById('ib-sel-copy-urls');
  const selArchive = document.getElementById('ib-sel-archive') || document.createElement('button');
  const selClear   = document.getElementById('ib-sel-clear');

  // MODEL LABEL MAP — pretty names for display
  const MODEL_LABELS = {
    'bandits-blue':         'Bandits Blue',
    'bandits-glossy-black': 'Bandits Glossy Black',
    'bandits-green':        'Bandits Green',
    'bandits-matte-black':  'Bandits Matte Black',
    'bandits-tortoise':     'Bandits Tortoise',
    'outback-black':        'Outback Black',
    'outback-blue':         'Outback Blue',
    'outback-green':        'Outback Green',
    'outback-red':          'Outback Red',
    'rasta-brown':          'Rasta Brown',
    'rasta-red':            'Rasta Red',
  };

  // -- Favorites helpers -------------------------------------------------------

  function urlToPath(url) {
    return (url || '').replace(/^\/api\/images\//, '');
  }
  function pathToUrl(p) {
    return '/api/images/' + p;
  }

  async function loadFavoritesFromServer() {
    try {
      const r = await fetch('/api/schedule/favorites');
      const d = await r.json();
      const paths = Array.isArray(d.favorites) ? d.favorites : [];
      favorites = new Set(paths.map(pathToUrl));
    } catch (e) {
      // Server unreachable -- keep favorites as empty Set rather than crashing.
      favorites = new Set();
    }
    // One-time migration of any pre-existing localStorage favorites into the
    // server store. Drains the legacy ib-favorites key so it never overrides
    // the server store on next page load.
    try {
      const legacy = JSON.parse(localStorage.getItem('ib-favorites') || '[]');
      if (Array.isArray(legacy) && legacy.length) {
        await Promise.allSettled(legacy.map(url =>
          fetch('/api/schedule/favorites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: urlToPath(url), action: 'add' }),
          })
        ));
        legacy.forEach(url => favorites.add(url));
        localStorage.removeItem('ib-favorites');
      }
    } catch (e) { /* ignore */ }
  }

  async function toggleFav(url) {
    const path = urlToPath(url);
    // Optimistic local toggle so the UI stays snappy.
    const willFav = !favorites.has(url);
    if (willFav) favorites.add(url); else favorites.delete(url);
    try {
      await fetch('/api/schedule/favorites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, action: 'toggle' }),
      });
    } catch (e) {
      // Server write failed -- roll back local state.
      if (willFav) favorites.delete(url); else favorites.add(url);
    }
  }

  // -- Multi-select ------------------------------------------------------------

  function updateSelBar() {
    const n = selected.size;
    grid.classList.toggle('selecting', n > 0);
    selBar.classList.toggle('hidden', n === 0);
    selCount.textContent = `${n} selected`;
    // Any selection change disarms a pending bulk-archive (count would be stale).
    resetSelArchiveBtn();
  }

  // Reflect a single thumb's selected state in the DOM (border + checkbox).
  function paintThumb(div) {
    if (!div) return;
    const url = div.dataset.url;
    const isSel = selected.has(url);
    div.classList.toggle('selected', isSel);
    const btn = div.querySelector('.ib-sel-btn');
    if (btn) {
      btn.classList.toggle('checked', isSel);
      btn.textContent = isSel ? '✓' : '';
      btn.title = isSel ? 'Deselect' : 'Select';
    }
  }

  function toggleSelect(url, div) {
    if (selected.has(url)) selected.delete(url); else selected.add(url);
    paintThumb(div);
    updateSelBar();
  }

  function clearSelection() {
    selected.clear();
    grid.querySelectorAll('.ib-thumb').forEach(paintThumb);
    updateSelBar();
  }

  function copySelected(asUrls) {
    if (selected.size === 0) return;
    const items = [...selected].map(url =>
      asUrls ? (window.location.origin + url) : url.replace(/^\/api\/images\//, '')
    );
    const btn = asUrls ? selCopyUrl : selCopy;
    const label = btn.textContent;
    navigator.clipboard.writeText(items.join('\n')).then(() => {
      btn.textContent = `Copied ${items.length}!`;
      setTimeout(() => btn.textContent = label, 1500);
    });
  }

  // Bulk archive -- two-click confirm (count shown), then archive each selected
  // image via the same /api/image-bank/archive endpoint as the lightbox button.
  let selArchiveArmed = false;
  let selArchiveTimer = null;

  function resetSelArchiveBtn() {
    selArchiveArmed = false;
    if (selArchiveTimer) { clearTimeout(selArchiveTimer); selArchiveTimer = null; }
    selArchive.textContent = 'Archive';
    selArchive.classList.remove('arming');
    selArchive.disabled = false;
  }

  async function archiveSelected() {
    const urls = [...selected];
    if (urls.length === 0) return;
    selArchive.disabled = true;
    selArchive.textContent = `Archiving ${urls.length}…`;
    const results = await Promise.allSettled(urls.map(url =>
      fetch('/api/image-bank/archive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: urlToPath(url) }),
      }).then(r => r.json()).then(d => { if (!d.ok) throw new Error(d.error || 'failed'); return url; })
    ));
    const okSet = new Set();
    results.forEach((res, i) => { if (res.status === 'fulfilled') okSet.add(urls[i]); });
    // Drop successfully archived images from local state so they leave the grid.
    allImages = allImages.filter(i => !okSet.has(i.url));
    okSet.forEach(u => { selected.delete(u); favorites.delete(u); });
    const failed = urls.length - okSet.size;
    applyFilters();   // rebuilds filtered + grid + count
    updateSelBar();   // also disarms + resets the button
    if (failed) {
      selArchive.textContent = `${okSet.size} done, ${failed} failed`;
      selArchive.disabled = true;
      setTimeout(resetSelArchiveBtn, 2200);
    }
  }

  // -- Init / load -------------------------------------------------------------

  async function init() {
    const tabEl = document.querySelector('.tab[data-tab="image-bank"]');
    if (!tabEl) return;
    const observer = new MutationObserver(() => {
      if (tabEl.classList.contains('active')) load();
    });
    observer.observe(tabEl, { attributes: true, attributeFilter: ['class'] });
    if (tabEl.classList.contains('active')) load();
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => {
        refreshBtn.disabled = true;
        load().finally(() => { refreshBtn.disabled = false; });
      });
    }

    // Zoom slider -- adjusts thumb size via CSS var. Persists in localStorage.
    const zoom = document.getElementById('ib-zoom');
    if (zoom) {
      const stored = parseInt(localStorage.getItem('ib-zoom') || '', 10);
      if (!isNaN(stored) && stored >= 100 && stored <= 320) zoom.value = String(stored);
      const applyZoom = (px) => {
        document.documentElement.style.setProperty('--ib-thumb-size', px + 'px');
      };
      applyZoom(parseInt(zoom.value, 10));
      zoom.addEventListener('input', () => {
        const px = parseInt(zoom.value, 10);
        applyZoom(px);
        localStorage.setItem('ib-zoom', String(px));
      });
    }
  }

  async function load() {
    loading.style.display = '';
    grid.querySelectorAll('.ib-thumb, .ib-empty').forEach(el => el.remove());
    count.textContent = '—';
    try {
      // Favorites + image list in parallel; render after both settle so the
      // first paint already has correct hearts (no flicker from undefined ->
      // server state).
      const [res] = await Promise.all([
        fetch('/api/image-bank'),
        loadFavoritesFromServer(),
      ]);
      allImages = await res.json();
      buildModelChips();
      applyFilters();
    } catch (e) {
      loading.textContent = 'Failed to load images.';
    }
  }

  function buildModelChips() {
    const models = [...new Set(allImages.filter(i => i.model).map(i => i.model))].sort();
    modelGrp.innerHTML = '<button class="ib-chip active" data-filter-model="all">All models</button>';
    models.forEach(m => {
      const btn = document.createElement('button');
      btn.className = 'ib-chip';
      btn.dataset.filterModel = m;
      btn.textContent = MODEL_LABELS[m] || m;
      modelGrp.appendChild(btn);
    });
    modelGrp.querySelectorAll('.ib-chip').forEach(b => b.addEventListener('click', onModelChip));
  }

  function applyFilters() {
    const q = search.value.trim().toLowerCase();
    filtered = allImages.filter(img => {
      if (activeType === 'favorites') return favorites.has(img.url);
      if (activeType !== 'all' && img.type !== activeType) return false;
      if (activeModel !== 'all' && img.model !== activeModel) return false;
      if (q && !img.filename.toLowerCase().includes(q)) return false;
      return true;
    });
    renderGrid();
    count.textContent = `${filtered.length} image${filtered.length !== 1 ? 's' : ''}`;

    // Model chips: hide for brand/all/favorites
    const showModel = activeType !== 'brand' && activeType !== 'all' && activeType !== 'favorites';
    modelGrp.style.display = showModel ? 'flex' : 'none';

    // Copy Paths button: only visible in favorites view
    copyPaths.classList.toggle('hidden', activeType !== 'favorites');
  }

  function renderGrid() {
    loading.style.display = 'none';
    grid.querySelectorAll('.ib-thumb').forEach(el => el.remove());

    if (filtered.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'ib-empty';
      empty.textContent = activeType === 'favorites' ? 'No favorites yet. Click ♥ on any image.' : 'No images match.';
      grid.appendChild(empty);
      return;
    }
    grid.querySelectorAll('.ib-empty').forEach(el => el.remove());

    filtered.forEach((img, idx) => {
      const div = document.createElement('div');
      div.className = 'ib-thumb' + (selected.has(img.url) ? ' selected' : '');
      div.dataset.idx = idx;
      div.dataset.url = img.url;

      const imgEl = document.createElement('img');
      imgEl.loading = 'lazy';
      imgEl.decoding = 'async';
      // Use cached 240px JPEG for the grid (-> ~15KB instead of ~1.5MB full PNG).
      // Falls back to the original if the thumb endpoint errors.
      imgEl.src = img.url.replace('/api/images/', '/api/thumb/') + '?w=240';
      imgEl.dataset.fullUrl = img.url;
      imgEl.addEventListener('error', function once() {
        imgEl.removeEventListener('error', once);
        imgEl.src = img.url;
      }, { once: true });
      imgEl.alt = img.filename;

      const badge = document.createElement('span');
      badge.className = `ib-badge ib-badge--${img.type}`;
      badge.textContent = img.type === 'brand' ? 'brand' : (MODEL_LABELS[img.model] || img.model || '');

      // Heart button
      const heart = document.createElement('button');
      heart.className = 'ib-fav-btn' + (favorites.has(img.url) ? ' faved' : '');
      heart.title = favorites.has(img.url) ? 'Remove from favorites' : 'Add to favorites';
      heart.textContent = favorites.has(img.url) ? '♥' : '♡';
      heart.addEventListener('click', e => {
        e.stopPropagation();
        toggleFav(img.url);
        heart.classList.toggle('faved', favorites.has(img.url));
        heart.textContent = favorites.has(img.url) ? '♥' : '♡';
        heart.title = favorites.has(img.url) ? 'Remove from favorites' : 'Add to favorites';
        // If in favorites view, re-render to remove unfaved item
        if (activeType === 'favorites') applyFilters();
        // Keep lightbox fav button in sync if open
        if (!lb.classList.contains('hidden') && filtered[lbIndex] && filtered[lbIndex].url === img.url) {
          syncLbFav(img.url);
        }
      });

      // Select checkbox (top-left). Always toggles selection, regardless of
      // mode -- clicking it on a fresh grid is how you start selecting.
      const selBtn = document.createElement('button');
      selBtn.className = 'ib-sel-btn' + (selected.has(img.url) ? ' checked' : '');
      selBtn.textContent = selected.has(img.url) ? '✓' : '';
      selBtn.title = selected.has(img.url) ? 'Deselect' : 'Select';
      selBtn.addEventListener('click', e => {
        e.stopPropagation();
        toggleSelect(img.url, div);
      });

      div.appendChild(imgEl);
      div.appendChild(badge);
      div.appendChild(heart);
      div.appendChild(selBtn);
      // In selection mode a plain thumb click toggles selection; otherwise it
      // opens the lightbox.
      div.addEventListener('click', () => {
        if (selected.size > 0) toggleSelect(img.url, div);
        else openLightbox(idx);
      });
      grid.appendChild(div);
    });
  }

  // -- Lightbox ----------------------------------------------------------------

  function syncLbFav(url) {
    const isFaved = favorites.has(url);
    lbFav.textContent = isFaved ? '♥ Unfavorite' : '♡ Favorite';
    lbFav.classList.toggle('faved', isFaved);
  }

  function openLightbox(idx) {
    lbIndex = idx;
    showLb();
    lb.classList.remove('hidden');
  }

  function showLb() {
    const img = filtered[lbIndex];
    lbImg.src = img.url;
    lbImg.alt = img.filename;
    lbType.textContent = img.type;
    lbType.className = `ib-lb-type ib-badge ib-badge--${img.type}`;
    lbModel.textContent = img.model ? (MODEL_LABELS[img.model] || img.model) : '';
    lbModel.style.display = img.model ? '' : 'none';
    lbName.textContent = img.filename;
    lbDl.href = img.url;
    lbDl.download = img.filename;
    lbPrev.disabled = lbIndex === 0;
    lbNext.disabled = lbIndex === filtered.length - 1;
    syncLbFav(img.url);
    resetArchiveBtn();
  }

  function closeLightbox() { lb.classList.add('hidden'); resetArchiveBtn(); }

  lbClose.addEventListener('click', closeLightbox);
  lbBack.addEventListener('click', closeLightbox);
  lbPrev.addEventListener('click', () => { if (lbIndex > 0) { lbIndex--; showLb(); } });
  lbNext.addEventListener('click', () => { if (lbIndex < filtered.length - 1) { lbIndex++; showLb(); } });

  lbCopy.addEventListener('click', () => {
    const url = window.location.origin + filtered[lbIndex].url;
    navigator.clipboard.writeText(url).then(() => {
      lbCopy.textContent = 'Copied!';
      setTimeout(() => lbCopy.textContent = 'Copy URL', 1500);
    });
  });

  lbFav.addEventListener('click', () => {
    const img = filtered[lbIndex];
    toggleFav(img.url);
    syncLbFav(img.url);
    // Sync heart on the thumbnail in the grid
    const thumb = grid.querySelector(`.ib-thumb[data-idx="${lbIndex}"]`);
    if (thumb) {
      const heart = thumb.querySelector('.ib-fav-btn');
      if (heart) {
        heart.classList.toggle('faved', favorites.has(img.url));
        heart.textContent = favorites.has(img.url) ? '♥' : '♡';
      }
    }
    if (activeType === 'favorites') {
      closeLightbox();
      applyFilters();
    }
  });

  // -- Archive (move out of bank) ----------------------------------------------
  // Two-click confirm so a stray click in the lightbox can't archive an image.
  // The action MOVES the file to contents/archive/ (recoverable, never deleted).

  let archiveArmed = false;
  let archiveTimer = null;

  function resetArchiveBtn() {
    archiveArmed = false;
    if (archiveTimer) { clearTimeout(archiveTimer); archiveTimer = null; }
    lbArchive.textContent = 'Archive';
    lbArchive.classList.remove('arming');
    lbArchive.disabled = false;
  }

  async function archiveImage(img) {
    lbArchive.disabled = true;
    lbArchive.textContent = 'Archiving…';
    try {
      const r = await fetch('/api/image-bank/archive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: urlToPath(img.url) }),
      });
      const d = await r.json();
      if (!d.ok) throw new Error(d.error || 'archive failed');
      // Drop it from local state so it disappears from the bank immediately.
      allImages = allImages.filter(i => i.url !== img.url);
      favorites.delete(img.url);
      selected.delete(img.url);
      closeLightbox();
      resetArchiveBtn();
      applyFilters();   // rebuilds filtered + grid + count
      updateSelBar();
    } catch (e) {
      lbArchive.textContent = 'Archive failed';
      setTimeout(resetArchiveBtn, 1800);
    }
  }

  lbArchive.addEventListener('click', () => {
    if (!archiveArmed) {
      archiveArmed = true;
      lbArchive.textContent = 'Click again to archive';
      lbArchive.classList.add('arming');
      archiveTimer = setTimeout(resetArchiveBtn, 3000);
      return;
    }
    archiveImage(filtered[lbIndex]);
  });

  // -- Copy All Paths ----------------------------------------------------------

  copyPaths.addEventListener('click', () => {
    // Strip /api/images/ prefix to get relative project paths
    const paths = [...favorites].map(url => url.replace(/^\/api\/images\//, ''));
    if (paths.length === 0) {
      copyPaths.textContent = 'None saved';
      setTimeout(() => copyPaths.textContent = 'Copy All Paths', 1500);
      return;
    }
    navigator.clipboard.writeText(paths.join('\n')).then(() => {
      copyPaths.textContent = `Copied ${paths.length} paths!`;
      setTimeout(() => copyPaths.textContent = 'Copy All Paths', 2000);
    });
  });

  // -- Selection bar wiring ----------------------------------------------------

  selCopy.addEventListener('click', () => copySelected(false));
  selCopyUrl.addEventListener('click', () => copySelected(true));
  selClear.addEventListener('click', clearSelection);

  selArchive.addEventListener('click', () => {
    if (selected.size === 0) return;
    if (!selArchiveArmed) {
      selArchiveArmed = true;
      selArchive.textContent = `Click again to archive ${selected.size}`;
      selArchive.classList.add('arming');
      selArchiveTimer = setTimeout(resetSelArchiveBtn, 3000);
      return;
    }
    archiveSelected();
  });

  // -- Keyboard ----------------------------------------------------------------

  document.addEventListener('keydown', e => {
    if (lb.classList.contains('hidden')) {
      // No lightbox open -- Esc clears an active selection.
      if (e.key === 'Escape' && selected.size > 0) clearSelection();
      return;
    }
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft' && lbIndex > 0) { lbIndex--; showLb(); }
    if (e.key === 'ArrowRight' && lbIndex < filtered.length - 1) { lbIndex++; showLb(); }
  });

  // -- Type / model chips ------------------------------------------------------

  typeGrp.querySelectorAll('.ib-chip').forEach(btn => btn.addEventListener('click', onTypeChip));

  function onTypeChip(e) {
    activeType = e.currentTarget.dataset.filterType;
    activeModel = 'all';
    typeGrp.querySelectorAll('.ib-chip').forEach(b => b.classList.toggle('active', b === e.currentTarget));
    modelGrp.querySelectorAll('.ib-chip').forEach(b => b.classList.toggle('active', b.dataset.filterModel === 'all'));
    applyFilters();
  }

  function onModelChip(e) {
    activeModel = e.currentTarget.dataset.filterModel;
    modelGrp.querySelectorAll('.ib-chip').forEach(b => b.classList.toggle('active', b === e.currentTarget));
    applyFilters();
  }

  search.addEventListener('input', applyFilters);

  init();
})();
