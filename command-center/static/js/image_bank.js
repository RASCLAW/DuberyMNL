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
  const lbFav      = document.getElementById('ib-lb-fav') || document.createElement('button');
  const lbClose    = document.getElementById('ib-lb-close');
  const lbPrev     = document.getElementById('ib-lb-prev');
  const lbNext     = document.getElementById('ib-lb-next');
  const lbBack     = document.getElementById('ib-lb-backdrop');
  const copyPaths  = document.getElementById('ib-copy-paths') || document.createElement('button');
  const refreshBtn = document.getElementById('ib-refresh');

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
      div.className = 'ib-thumb';
      div.dataset.idx = idx;

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

      div.appendChild(imgEl);
      div.appendChild(badge);
      div.appendChild(heart);
      div.addEventListener('click', () => openLightbox(idx));
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
  }

  function closeLightbox() { lb.classList.add('hidden'); }

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

  // -- Keyboard ----------------------------------------------------------------

  document.addEventListener('keydown', e => {
    if (lb.classList.contains('hidden')) return;
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
