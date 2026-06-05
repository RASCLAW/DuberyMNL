/* Video Bank tab -- mirrors image_bank.js but for Veo .mp4/.webm clips.
   Reuses the .ib-* layout/lightbox/collection styling; talks to the dedicated
   /api/video-bank* endpoints (separate favorites + collections stores from the
   image bank). The lightbox plays a <video> instead of showing an <img>. */
(function () {
  let allVideos = [];
  let filtered = [];
  let activeType = 'all';      // all | favorites | collections
  let activeSeries = 'all';
  let activeRatio = 'all';     // all | "9:16" | "16:9" | ... (from sidecar aspect_ratio)
  let lbIndex = 0;
  let lbSource = [];
  // Favorites: server-side at /api/video-bank/favorites. Keys on disk are
  // project-relative PATHS ("contents/..."); the in-memory Set holds URLs
  // (/api/images/...) for easy match against item.url.
  let favorites = new Set();
  // Ad-hoc multi-select (Google-Photos style). URLs. Ephemeral.
  let selected = new Set();
  // Collections: server-side at /api/video-bank/collections. {name: [paths]}.
  let collections = {};
  let collModalName = null;

  const grid       = document.getElementById('vb-grid');
  const loading    = document.getElementById('vb-loading');
  const count      = document.getElementById('vb-count');
  const search     = document.getElementById('vb-search');
  const typeGrp    = document.getElementById('vb-type-filters');
  const seriesGrp  = document.getElementById('vb-series-filters');
  const ratioGrp   = document.getElementById('vb-ratio-filters');
  const lb         = document.getElementById('vb-lightbox');
  const lbVideo    = document.getElementById('vb-video');
  const lbSeries   = document.getElementById('vb-lb-series');
  const lbName     = document.getElementById('vb-lb-name');
  const lbPos      = document.getElementById('vb-lb-pos');
  const lbDl       = document.getElementById('vb-lb-dl');
  const lbCopy     = document.getElementById('vb-lb-copy');
  const lbFav      = document.getElementById('vb-lb-fav') || document.createElement('button');
  const lbClose    = document.getElementById('vb-lb-close');
  const lbPrev     = document.getElementById('vb-lb-prev');
  const lbNext     = document.getElementById('vb-lb-next');
  const lbBack     = document.getElementById('vb-lb-backdrop');
  const copyPaths  = document.getElementById('vb-copy-paths') || document.createElement('button');
  const refreshBtn = document.getElementById('vb-refresh');
  const selBar     = document.getElementById('vb-selbar');
  const selCount   = document.getElementById('vb-selbar-count');
  const selCopy    = document.getElementById('vb-sel-copy');
  const selCopyUrl = document.getElementById('vb-sel-copy-urls');
  const selDownload= document.getElementById('vb-sel-download') || document.createElement('button');
  const selClear   = document.getElementById('vb-sel-clear');
  const selCollBtn = document.getElementById('vb-sel-collection') || document.createElement('button');

  // Collection picker modal
  const collpick         = document.getElementById('vb-collpick');
  const collpickBack     = document.getElementById('vb-collpick-backdrop');
  const collpickClose    = document.getElementById('vb-collpick-close');
  const collpickHead     = document.getElementById('vb-collpick-head');
  const collpickExisting = document.getElementById('vb-collpick-existing');
  const collpickInput    = document.getElementById('vb-collpick-input');
  const collpickCreate   = document.getElementById('vb-collpick-create');

  // Collection view modal
  const collModal       = document.getElementById('vb-collmodal');
  const collModalBack   = document.getElementById('vb-collmodal-backdrop');
  const collModalClose  = document.getElementById('vb-collmodal-close');
  const collModalTitle  = document.getElementById('vb-collmodal-title');
  const collModalTitleIn= document.getElementById('vb-collmodal-title-input');
  const collModalCount  = document.getElementById('vb-collmodal-count');
  const collModalGrid   = document.getElementById('vb-collmodal-grid');
  const collModalAdd    = document.getElementById('vb-collmodal-add');
  const collModalRename = document.getElementById('vb-collmodal-rename');
  const collModalCopy   = document.getElementById('vb-collmodal-copy');
  const collModalDelete = document.getElementById('vb-collmodal-delete');

  // Add-videos picker
  const cellAdd        = document.getElementById('vb-celladd');
  const cellAddBack    = document.getElementById('vb-celladd-backdrop');
  const cellAddClose   = document.getElementById('vb-celladd-close');
  const cellAddTitle   = document.getElementById('vb-celladd-title');
  const cellAddConfirm = document.getElementById('vb-celladd-confirm');
  const cellAddGrid    = document.getElementById('vb-celladd-grid');

  let dragSrcIdx = null;
  let cellAddSel = new Set();

  // -- Path/URL helpers --------------------------------------------------------

  function urlToPath(url) { return (url || '').replace(/^\/api\/images\//, ''); }
  function pathToUrl(p)   { return '/api/images/' + p; }
  function thumbUrl(path, w) { return '/api/video-thumb/' + path + '?w=' + (w || 240); }

  // Create a poster <img> for a video path; on error (ffmpeg unavailable / short
  // clip), swap it in place for an inline muted <video> showing the first frame.
  function makePosterEl(path, withPlayBadge) {
    const wrap = document.createDocumentFragment();
    const im = document.createElement('img');
    im.loading = 'lazy';
    im.decoding = 'async';
    im.draggable = false;
    im.alt = path.split('/').pop();
    im.src = thumbUrl(path, 240);
    im.addEventListener('error', function once() {
      im.removeEventListener('error', once);
      const v = document.createElement('video');
      v.className = 'vb-thumb-vid';
      v.preload = 'metadata';
      v.muted = true;
      v.playsInline = true;
      v.src = pathToUrl(path) + '#t=0.1';   // nudge so the first frame paints
      if (im.parentNode) im.parentNode.replaceChild(v, im);
    }, { once: true });
    wrap.appendChild(im);
    if (withPlayBadge) {
      const badge = document.createElement('span');
      badge.className = 'vb-play-badge';
      wrap.appendChild(badge);
    }
    return wrap;
  }

  // -- Favorites ---------------------------------------------------------------

  async function loadFavoritesFromServer() {
    try {
      const r = await fetch('/api/video-bank/favorites');
      const d = await r.json();
      const paths = Array.isArray(d.favorites) ? d.favorites : [];
      favorites = new Set(paths.map(pathToUrl));
    } catch (e) {
      favorites = new Set();
    }
  }

  async function toggleFav(url) {
    const path = urlToPath(url);
    const willFav = !favorites.has(url);
    if (willFav) favorites.add(url); else favorites.delete(url);
    try {
      await fetch('/api/video-bank/favorites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, action: 'toggle' }),
      });
    } catch (e) {
      if (willFav) favorites.delete(url); else favorites.add(url);
    }
  }

  // -- Collections -------------------------------------------------------------

  async function loadCollectionsFromServer() {
    try {
      const r = await fetch('/api/video-bank/collections');
      const d = await r.json();
      collections = (d && d.collections) ? d.collections : {};
    } catch (e) {
      collections = {};
    }
  }

  // -- Multi-select ------------------------------------------------------------

  function updateSelBar() {
    const n = selected.size;
    grid.classList.toggle('selecting', n > 0);
    selBar.classList.toggle('hidden', n === 0);
    selCount.textContent = `${n} selected`;
    selCollBtn.classList.toggle('hidden', !(n > 0 && activeType === 'favorites'));
  }

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
      asUrls ? (window.location.origin + url) : urlToPath(url)
    );
    const btn = asUrls ? selCopyUrl : selCopy;
    const label = btn.textContent;
    navigator.clipboard.writeText(items.join('\n')).then(() => {
      btn.textContent = `Copied ${items.length}!`;
      setTimeout(() => btn.textContent = label, 1500);
    });
  }

  // Bulk download -- POST selected paths, get a single ZIP blob back, save it.
  async function downloadSelected() {
    if (selected.size === 0) return;
    const paths = [...selected].map(urlToPath);
    const label = selDownload.dataset.label || selDownload.textContent;
    selDownload.dataset.label = label;
    selDownload.disabled = true;
    selDownload.textContent = `Zipping ${paths.length}…`;
    try {
      const r = await fetch('/api/video-bank/download-zip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paths }),
      });
      if (!r.ok) throw new Error('zip failed');
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dubery-videos-${paths.length}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      selDownload.textContent = 'Downloaded!';
    } catch (e) {
      selDownload.textContent = 'Download failed';
    }
    setTimeout(() => { selDownload.textContent = label; selDownload.disabled = false; }, 1600);
  }

  // -- Init / load -------------------------------------------------------------

  async function init() {
    const tabEl = document.querySelector('.tab[data-tab="video-bank"]');
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
    // Zoom slider -- reuses the shared --ib-thumb-size CSS var (same grid rule).
    const zoom = document.getElementById('vb-zoom');
    if (zoom) {
      const stored = parseInt(localStorage.getItem('vb-zoom') || '', 10);
      if (!isNaN(stored) && stored >= 100 && stored <= 320) zoom.value = String(stored);
      const applyZoom = (px) => document.documentElement.style.setProperty('--ib-thumb-size', px + 'px');
      applyZoom(parseInt(zoom.value, 10));
      zoom.addEventListener('input', () => {
        const px = parseInt(zoom.value, 10);
        applyZoom(px);
        localStorage.setItem('vb-zoom', String(px));
      });
    }
  }

  async function load() {
    loading.style.display = '';
    grid.querySelectorAll('.ib-thumb, .ib-empty, .ib-coll-card, .ib-coll-series').forEach(el => el.remove());
    count.textContent = '—';
    try {
      const [res] = await Promise.all([
        fetch('/api/video-bank'),
        loadFavoritesFromServer(),
        loadCollectionsFromServer(),
      ]);
      allVideos = await res.json();
      buildSeriesChips();
      buildRatioChips();
      applyFilters();
    } catch (e) {
      console.error('[video-bank] load failed:', e && e.stack || e);
      loading.textContent = 'Failed to load videos.';
    }
  }

  function buildSeriesChips() {
    const series = [...new Set(allVideos.filter(v => v.series).map(v => v.series))].sort();
    seriesGrp.innerHTML = '<button class="ib-chip active" data-filter-series="all">All series</button>';
    series.forEach(s => {
      const btn = document.createElement('button');
      btn.className = 'ib-chip';
      btn.dataset.filterSeries = s;
      btn.textContent = s;
      seriesGrp.appendChild(btn);
    });
    seriesGrp.querySelectorAll('.ib-chip').forEach(b => b.addEventListener('click', onSeriesChip));
  }

  // One pill per aspect ratio actually present (e.g. 9:16, 16:9). Built from the
  // sidecar `aspect_ratio` field; videos without a sidecar have no ratio and only
  // show under "All ratios". Self-adjusts if a new ratio (4:5, 1:1) ever appears.
  function buildRatioChips() {
    const ratios = [...new Set(allVideos.map(v => v.aspect_ratio).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b));
    ratioGrp.innerHTML = '<button class="ib-chip active" data-filter-ratio="all">All ratios</button>';
    ratios.forEach(r => {
      const btn = document.createElement('button');
      btn.className = 'ib-chip';
      btn.dataset.filterRatio = r;
      btn.textContent = r;
      ratioGrp.appendChild(btn);
    });
    ratioGrp.querySelectorAll('.ib-chip').forEach(b => b.addEventListener('click', onRatioChip));
  }

  function applyFilters() {
    if (activeType === 'collections') {
      filtered = [];
      renderCollections();
      const n = Object.keys(collections).length;
      count.textContent = `${n} collection${n !== 1 ? 's' : ''}`;
      seriesGrp.style.display = 'none';
      ratioGrp.style.display = 'none';
      copyPaths.classList.add('hidden');
      selCollBtn.classList.add('hidden');
      return;
    }
    const q = search.value.trim().toLowerCase();
    filtered = allVideos.filter(v => {
      if (activeType === 'favorites') {
        if (!favorites.has(v.url)) return false;
        if (q && !v.filename.toLowerCase().includes(q)) return false;
        return true;
      }
      if (activeSeries !== 'all' && v.series !== activeSeries) return false;
      if (activeRatio !== 'all' && v.aspect_ratio !== activeRatio) return false;
      if (q && !v.filename.toLowerCase().includes(q)) return false;
      return true;
    });
    renderGrid();
    count.textContent = `${filtered.length} video${filtered.length !== 1 ? 's' : ''}`;

    // Series + ratio chips only in the "All" view.
    seriesGrp.style.display = activeType === 'all' ? 'flex' : 'none';
    ratioGrp.style.display = activeType === 'all' ? 'flex' : 'none';
    copyPaths.classList.toggle('hidden', activeType !== 'favorites');
    selCollBtn.classList.toggle('hidden', !(selected.size > 0 && activeType === 'favorites'));
  }

  function renderGrid() {
    loading.style.display = 'none';
    grid.classList.remove('coll-mode');
    grid.querySelectorAll('.ib-thumb, .ib-coll-card, .ib-coll-series').forEach(el => el.remove());

    if (filtered.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'ib-empty';
      empty.textContent = activeType === 'favorites' ? 'No favorites yet. Click ♥ on any video.' : 'No videos match.';
      grid.appendChild(empty);
      return;
    }
    grid.querySelectorAll('.ib-empty').forEach(el => el.remove());

    filtered.forEach((vid, idx) => {
      const div = document.createElement('div');
      div.className = 'ib-thumb' + (selected.has(vid.url) ? ' selected' : '');
      div.dataset.idx = idx;
      div.dataset.url = vid.url;

      div.appendChild(makePosterEl(urlToPath(vid.url), true));

      const badge = document.createElement('span');
      badge.className = 'ib-badge';
      badge.textContent = vid.series || '';

      // Optional size tag bottom-right.
      if (vid.size_kb) {
        const tag = document.createElement('span');
        tag.className = 'vb-dur-badge';
        tag.textContent = vid.size_kb >= 1024 ? `${(vid.size_kb / 1024).toFixed(1)}MB` : `${vid.size_kb}KB`;
        div.appendChild(tag);
      }

      const heart = document.createElement('button');
      heart.className = 'ib-fav-btn' + (favorites.has(vid.url) ? ' faved' : '');
      heart.title = favorites.has(vid.url) ? 'Remove from favorites' : 'Add to favorites';
      heart.textContent = favorites.has(vid.url) ? '♥' : '♡';
      heart.addEventListener('click', e => {
        e.stopPropagation();
        toggleFav(vid.url);
        heart.classList.toggle('faved', favorites.has(vid.url));
        heart.textContent = favorites.has(vid.url) ? '♥' : '♡';
        heart.title = favorites.has(vid.url) ? 'Remove from favorites' : 'Add to favorites';
        if (activeType === 'favorites') applyFilters();
        if (!lb.classList.contains('hidden') && lbSource[lbIndex] && lbSource[lbIndex].url === vid.url) {
          syncLbFav(vid.url);
        }
      });

      const selBtn = document.createElement('button');
      selBtn.className = 'ib-sel-btn' + (selected.has(vid.url) ? ' checked' : '');
      selBtn.textContent = selected.has(vid.url) ? '✓' : '';
      selBtn.title = selected.has(vid.url) ? 'Deselect' : 'Select';
      selBtn.addEventListener('click', e => {
        e.stopPropagation();
        toggleSelect(vid.url, div);
      });

      div.appendChild(badge);
      div.appendChild(heart);
      div.appendChild(selBtn);
      div.addEventListener('click', () => {
        if (selected.size > 0) toggleSelect(vid.url, div);
        else openLightbox(idx);
      });
      grid.appendChild(div);
    });
  }

  // -- Collections view (fanned-deck cards) ------------------------------------

  function collectionSeries(name) {
    const parts = name.split(/\s*[-–—]\s*/);
    return (parts.length > 1 && parts[0].trim()) ? parts[0].trim() : 'Other';
  }

  function buildCollCard(name) {
    const paths = collections[name] || [];
    const card = document.createElement('div');
    card.className = 'ib-coll-card';
    card.addEventListener('click', () => openCollModal(name));

    const deck = document.createElement('div');
    deck.className = 'ib-coll-deck';
    const fan = paths.slice(0, 3);
    [
      { cls: 'f3', path: fan[2] },
      { cls: 'f2', path: fan[1] },
      { cls: 'f1', path: fan[0] },
    ].forEach(o => {
      if (!o.path) return;
      const im = document.createElement('img');
      im.className = 'ib-coll-fan ' + o.cls;
      im.loading = 'lazy';
      im.decoding = 'async';
      im.alt = '';
      im.src = thumbUrl(o.path, 240);
      deck.appendChild(im);
    });
    const badge = document.createElement('span');
    badge.className = 'ib-coll-badge';
    badge.textContent = String(paths.length);
    deck.appendChild(badge);

    const nm = document.createElement('div');
    nm.className = 'ib-coll-name';
    nm.textContent = name;
    const sub = document.createElement('div');
    sub.className = 'ib-coll-sub';
    sub.textContent = `${paths.length} video${paths.length !== 1 ? 's' : ''}`;

    card.appendChild(deck);
    card.appendChild(nm);
    card.appendChild(sub);
    return card;
  }

  function renderCollections() {
    loading.style.display = 'none';
    grid.classList.add('coll-mode');
    grid.querySelectorAll('.ib-thumb, .ib-empty, .ib-coll-card, .ib-coll-series').forEach(el => el.remove());

    const names = Object.keys(collections);
    if (names.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'ib-empty';
      empty.textContent = 'No collections yet. Open the ♥ Favorites pill, select videos, then "Add to collection".';
      grid.appendChild(empty);
      return;
    }

    const groups = {};
    const order = [];
    names.forEach(name => {
      const series = collectionSeries(name);
      if (!groups[series]) { groups[series] = []; order.push(series); }
      groups[series].push(name);
    });

    order.forEach(series => {
      const section = document.createElement('div');
      section.className = 'ib-coll-series';
      const head = document.createElement('div');
      head.className = 'ib-coll-series-head';
      head.textContent = series;
      const sgrid = document.createElement('div');
      sgrid.className = 'ib-coll-series-grid';
      groups[series].forEach(name => sgrid.appendChild(buildCollCard(name)));
      section.appendChild(head);
      section.appendChild(sgrid);
      grid.appendChild(section);
    });
  }

  // -- Collection picker -------------------------------------------------------

  function openCollPick() {
    if (selected.size === 0) return;
    const n = selected.size;
    collpickHead.textContent = `Add ${n} video${n !== 1 ? 's' : ''} to collection`;
    collpickExisting.innerHTML = '';
    const names = Object.keys(collections);
    if (names.length === 0) {
      const none = document.createElement('span');
      none.className = 'small muted';
      none.textContent = 'No collections yet — create one below.';
      collpickExisting.appendChild(none);
    } else {
      names.forEach(name => {
        const chip = document.createElement('button');
        chip.className = 'ib-collpick-chip';
        chip.textContent = `${name} (${(collections[name] || []).length})`;
        chip.addEventListener('click', () => addToCollection(name));
        collpickExisting.appendChild(chip);
      });
    }
    collpickInput.value = '';
    collpick.classList.remove('hidden');
    setTimeout(() => collpickInput.focus(), 50);
  }

  function closeCollPick() { collpick.classList.add('hidden'); }

  async function addToCollection(name) {
    name = (name || '').trim();
    if (!name) { collpickInput.focus(); return; }
    if (selected.size === 0) return;
    const paths = [...selected].map(urlToPath);
    try {
      const r = await fetch('/api/video-bank/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, paths, action: 'add' }),
      });
      const d = await r.json();
      if (!d.ok) throw new Error(d.error || 'failed');
      collections = d.collections || collections;
      collpickHead.textContent = `Added ${paths.length} to "${name}"`;
      setTimeout(() => { closeCollPick(); clearSelection(); }, 800);
    } catch (e) {
      collpickHead.textContent = 'Add failed — try again';
    }
  }

  // -- Collection view modal ---------------------------------------------------

  function openCollModal(name) {
    collModalName = name;
    cancelRename();
    resetCollDel();
    renderCollModal();
    collModal.classList.remove('hidden');
  }

  function closeCollModal() {
    collModal.classList.add('hidden');
    collModalName = null;
    cancelRename();
    resetCollDel();
  }

  function renderCollModal() {
    const paths = collections[collModalName] || [];
    collModalTitle.textContent = collModalName || '';
    collModalCount.textContent = `${paths.length} video${paths.length !== 1 ? 's' : ''}`;
    collModalGrid.innerHTML = '';
    if (paths.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'ib-collmodal-empty';
      empty.textContent = 'This collection is empty.';
      collModalGrid.appendChild(empty);
      return;
    }
    paths.forEach((path, idx) => {
      const cell = document.createElement('div');
      cell.className = 'ib-collmodal-thumb';
      cell.draggable = true;
      cell.dataset.idx = idx;

      cell.addEventListener('dragstart', e => {
        dragSrcIdx = idx;
        cell.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        try { e.dataTransfer.setData('text/plain', String(idx)); } catch (_) {}
      });
      cell.addEventListener('dragend', () => {
        cell.classList.remove('dragging');
        collModalGrid.querySelectorAll('.dragover').forEach(el => el.classList.remove('dragover'));
      });
      cell.addEventListener('dragover', e => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        cell.classList.add('dragover');
      });
      cell.addEventListener('dragleave', () => cell.classList.remove('dragover'));
      cell.addEventListener('drop', e => {
        e.preventDefault();
        cell.classList.remove('dragover');
        if (dragSrcIdx === null || dragSrcIdx === idx) return;
        reorderCollection(dragSrcIdx, idx);
        dragSrcIdx = null;
      });

      cell.addEventListener('click', () => openLightboxFromCollection(idx));

      cell.appendChild(makePosterEl(path, true));
      const rm = document.createElement('button');
      rm.className = 'ib-collmodal-remove';
      rm.textContent = '×';
      rm.title = 'Remove from collection';
      rm.addEventListener('click', e => { e.stopPropagation(); removeFromCollection(path); });
      cell.appendChild(rm);
      collModalGrid.appendChild(cell);
    });
  }

  async function removeFromCollection(path) {
    if (!collModalName) return;
    const name = collModalName;
    try {
      const r = await fetch('/api/video-bank/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, paths: [path], action: 'remove' }),
      });
      const d = await r.json();
      if (!d.ok) throw new Error(d.error || 'failed');
      collections = d.collections || {};
      if (!collections[name]) closeCollModal();
      else renderCollModal();
      if (activeType === 'collections') applyFilters();
    } catch (e) { /* best-effort */ }
  }

  async function reorderCollection(from, to) {
    const cur = (collections[collModalName] || []).slice();
    if (from < 0 || from >= cur.length || to < 0 || to >= cur.length) return;
    const [moved] = cur.splice(from, 1);
    cur.splice(to, 0, moved);
    collections[collModalName] = cur;
    renderCollModal();
    if (activeType === 'collections') applyFilters();
    try {
      const r = await fetch('/api/video-bank/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: collModalName, paths: cur, action: 'reorder' }),
      });
      const d = await r.json();
      if (!d.ok) throw new Error(d.error || 'failed');
      collections = d.collections || collections;
    } catch (e) {
      await loadCollectionsFromServer();
      renderCollModal();
      if (activeType === 'collections') applyFilters();
    }
  }

  // -- Rename ------------------------------------------------------------------

  function startRename() {
    if (!collModalName) return;
    collModalTitleIn.value = collModalName;
    collModalTitleIn.placeholder = '';
    collModalTitle.classList.add('hidden');
    collModalTitleIn.classList.remove('hidden');
    collModalTitleIn.focus();
    collModalTitleIn.select();
  }

  function cancelRename() {
    collModalTitleIn.classList.add('hidden');
    collModalTitle.classList.remove('hidden');
  }

  async function commitRename() {
    const newName = collModalTitleIn.value.trim();
    if (!newName || newName === collModalName) { cancelRename(); return; }
    try {
      const r = await fetch('/api/video-bank/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: collModalName, new_name: newName, action: 'rename' }),
      });
      const d = await r.json();
      if (!d.ok) throw new Error(d.error || 'rename failed');
      collections = d.collections || collections;
      collModalName = d.name || newName;
      cancelRename();
      renderCollModal();
      if (activeType === 'collections') applyFilters();
    } catch (e) {
      collModalTitleIn.value = '';
      collModalTitleIn.placeholder = e.message || 'rename failed';
    }
  }

  // -- Copy paths --------------------------------------------------------------

  function copyCollectionPaths() {
    const paths = collections[collModalName] || [];
    if (!paths.length) return;
    navigator.clipboard.writeText(paths.join('\n')).then(() => {
      const label = collModalCopy.textContent;
      collModalCopy.textContent = `Copied ${paths.length}!`;
      setTimeout(() => collModalCopy.textContent = label, 1500);
    });
  }

  // -- Delete collection -------------------------------------------------------

  let collDelArmed = false;
  let collDelTimer = null;

  function resetCollDel() {
    collDelArmed = false;
    if (collDelTimer) { clearTimeout(collDelTimer); collDelTimer = null; }
    collModalDelete.textContent = 'Delete';
    collModalDelete.classList.remove('arming');
  }

  async function deleteCollection() {
    const name = collModalName;
    if (!name) return;
    try {
      const r = await fetch('/api/video-bank/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, action: 'delete' }),
      });
      const d = await r.json();
      if (!d.ok) throw new Error(d.error || 'failed');
      collections = d.collections || {};
      resetCollDel();
      closeCollModal();
      if (activeType === 'collections') applyFilters();
    } catch (e) {
      collModalDelete.textContent = 'Delete failed';
      setTimeout(resetCollDel, 1800);
    }
  }

  // -- Add-videos picker -------------------------------------------------------

  function openCellAdd() {
    if (!collModalName) return;
    const members = new Set(collections[collModalName] || []);
    const favPaths = [...favorites].map(urlToPath).filter(p => !members.has(p));
    cellAddSel = new Set();
    cellAddTitle.textContent = `Add videos to "${collModalName}"`;
    cellAddGrid.innerHTML = '';
    if (favPaths.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'ib-celladd-empty';
      empty.textContent = 'All your favorites are already in this collection. Favorite more videos (♥) to add them here.';
      cellAddGrid.appendChild(empty);
    } else {
      favPaths.forEach(path => {
        const cell = document.createElement('div');
        cell.className = 'ib-celladd-thumb';
        cell.appendChild(makePosterEl(path, true));
        const chk = document.createElement('span');
        chk.className = 'ib-celladd-check';
        chk.textContent = '';
        cell.appendChild(chk);
        cell.addEventListener('click', () => {
          if (cellAddSel.has(path)) { cellAddSel.delete(path); cell.classList.remove('sel'); chk.textContent = ''; }
          else { cellAddSel.add(path); cell.classList.add('sel'); chk.textContent = '✓'; }
          updateCellAddConfirm();
        });
        cellAddGrid.appendChild(cell);
      });
    }
    updateCellAddConfirm();
    cellAdd.classList.remove('hidden');
  }

  function updateCellAddConfirm() {
    const n = cellAddSel.size;
    cellAddConfirm.textContent = `Add ${n}`;
    cellAddConfirm.disabled = n === 0;
  }

  function closeCellAdd() { cellAdd.classList.add('hidden'); cellAddSel = new Set(); }

  async function confirmCellAdd() {
    if (cellAddSel.size === 0 || !collModalName) return;
    const paths = [...cellAddSel];
    try {
      const r = await fetch('/api/video-bank/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: collModalName, paths, action: 'add' }),
      });
      const d = await r.json();
      if (!d.ok) throw new Error(d.error || 'failed');
      collections = d.collections || collections;
      closeCellAdd();
      renderCollModal();
      if (activeType === 'collections') applyFilters();
    } catch (e) {
      cellAddConfirm.textContent = 'Add failed';
    }
  }

  // -- Player lightbox ---------------------------------------------------------

  function syncLbFav(url) {
    const isFaved = favorites.has(url);
    lbFav.textContent = isFaved ? '♥ Unfavorite' : '♡ Favorite';
    lbFav.classList.toggle('faved', isFaved);
  }

  function openLightbox(idx) {
    lbSource = filtered;
    lbIndex = idx;
    showLb();
    lb.classList.remove('hidden');
  }

  function openLightboxFromCollection(idx) {
    const paths = collections[collModalName] || [];
    if (!paths.length) return;
    lbSource = paths.map(p => {
      const url = pathToUrl(p);
      return allVideos.find(v => v.url === url) ||
             { url, filename: p.split('/').pop(), series: '' };
    });
    lbIndex = Math.max(0, Math.min(idx, lbSource.length - 1));
    showLb();
    lb.classList.remove('hidden');
  }

  function showLb() {
    const vid = lbSource[lbIndex];
    if (!vid) return;
    lbVideo.pause();
    lbVideo.src = vid.url;
    lbVideo.load();
    lbSeries.textContent = vid.series || '';
    lbSeries.style.display = vid.series ? '' : 'none';
    lbName.textContent = vid.filename;
    lbDl.href = vid.url;
    lbDl.download = vid.filename;
    lbPrev.disabled = lbIndex === 0;
    lbNext.disabled = lbIndex === lbSource.length - 1;
    if (lbPos) lbPos.textContent = lbSource.length ? `${lbIndex + 1} / ${lbSource.length}` : '';
    syncLbFav(vid.url);
  }

  function closeLightbox() {
    // Stop playback + free the stream so audio doesn't keep playing.
    lbVideo.pause();
    lbVideo.removeAttribute('src');
    lbVideo.load();
    lb.classList.add('hidden');
  }

  lbClose.addEventListener('click', closeLightbox);
  lbBack.addEventListener('click', closeLightbox);
  lbPrev.addEventListener('click', () => { if (lbIndex > 0) { lbIndex--; showLb(); } });
  lbNext.addEventListener('click', () => { if (lbIndex < lbSource.length - 1) { lbIndex++; showLb(); } });

  lbCopy.addEventListener('click', () => {
    const path = urlToPath(lbSource[lbIndex].url);
    navigator.clipboard.writeText(path).then(() => {
      lbCopy.textContent = 'Copied!';
      setTimeout(() => lbCopy.textContent = 'Copy path', 1500);
    });
  });

  lbFav.addEventListener('click', () => {
    const vid = lbSource[lbIndex];
    toggleFav(vid.url);
    syncLbFav(vid.url);
    const thumb = grid.querySelector(`.ib-thumb[data-url="${CSS.escape(vid.url)}"]`);
    if (thumb) {
      const heart = thumb.querySelector('.ib-fav-btn');
      if (heart) {
        heart.classList.toggle('faved', favorites.has(vid.url));
        heart.textContent = favorites.has(vid.url) ? '♥' : '♡';
      }
    }
    if (activeType === 'favorites') {
      closeLightbox();
      applyFilters();
    }
  });

  // -- Copy All Paths ----------------------------------------------------------

  copyPaths.addEventListener('click', () => {
    const paths = [...favorites].map(urlToPath);
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
  selDownload.addEventListener('click', downloadSelected);
  selClear.addEventListener('click', clearSelection);

  // -- Collections wiring ------------------------------------------------------

  selCollBtn.addEventListener('click', openCollPick);
  collpickClose.addEventListener('click', closeCollPick);
  collpickBack.addEventListener('click', closeCollPick);
  collpickCreate.addEventListener('click', () => addToCollection(collpickInput.value));
  collpickInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); addToCollection(collpickInput.value); }
  });
  collModalClose.addEventListener('click', closeCollModal);
  collModalBack.addEventListener('click', closeCollModal);
  collModalAdd.addEventListener('click', openCellAdd);
  collModalRename.addEventListener('click', startRename);
  collModalCopy.addEventListener('click', copyCollectionPaths);
  collModalDelete.addEventListener('click', () => {
    if (!collDelArmed) {
      collDelArmed = true;
      collModalDelete.textContent = 'Click again to delete';
      collModalDelete.classList.add('arming');
      collDelTimer = setTimeout(resetCollDel, 3000);
      return;
    }
    deleteCollection();
  });
  collModalTitleIn.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); commitRename(); }
    else if (e.key === 'Escape') { e.stopPropagation(); cancelRename(); }
  });
  collModalTitleIn.addEventListener('blur', cancelRename);

  cellAddClose.addEventListener('click', closeCellAdd);
  cellAddBack.addEventListener('click', closeCellAdd);
  cellAddConfirm.addEventListener('click', confirmCellAdd);

  // -- Keyboard ----------------------------------------------------------------

  document.addEventListener('keydown', e => {
    if (!lb.classList.contains('hidden')) {
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft' && lbIndex > 0) { lbIndex--; showLb(); }
      if (e.key === 'ArrowRight' && lbIndex < lbSource.length - 1) { lbIndex++; showLb(); }
      return;
    }
    if (cellAdd && !cellAdd.classList.contains('hidden')) {
      if (e.key === 'Escape') closeCellAdd();
      return;
    }
    if (collpick && !collpick.classList.contains('hidden')) {
      if (e.key === 'Escape') closeCollPick();
      return;
    }
    if (collModal && !collModal.classList.contains('hidden')) {
      if (e.key === 'Escape') closeCollModal();
      return;
    }
    if (e.key === 'Escape' && selected.size > 0) clearSelection();
  });

  // -- Type / series chips -----------------------------------------------------

  typeGrp.querySelectorAll('.ib-chip').forEach(btn => btn.addEventListener('click', onTypeChip));

  function onTypeChip(e) {
    activeType = e.currentTarget.dataset.filterType;
    activeSeries = 'all';
    activeRatio = 'all';
    typeGrp.querySelectorAll('.ib-chip').forEach(b => b.classList.toggle('active', b === e.currentTarget));
    seriesGrp.querySelectorAll('.ib-chip').forEach(b => b.classList.toggle('active', b.dataset.filterSeries === 'all'));
    ratioGrp.querySelectorAll('.ib-chip').forEach(b => b.classList.toggle('active', b.dataset.filterRatio === 'all'));
    applyFilters();
  }

  function onSeriesChip(e) {
    activeSeries = e.currentTarget.dataset.filterSeries;
    seriesGrp.querySelectorAll('.ib-chip').forEach(b => b.classList.toggle('active', b === e.currentTarget));
    applyFilters();
  }

  function onRatioChip(e) {
    activeRatio = e.currentTarget.dataset.filterRatio;
    ratioGrp.querySelectorAll('.ib-chip').forEach(b => b.classList.toggle('active', b === e.currentTarget));
    applyFilters();
  }

  search.addEventListener('input', applyFilters);

  init();
})();
