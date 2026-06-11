/* Image Bank tab */
(function () {
  let allImages = [];
  let filtered = [];
  let activeType = 'all';
  let activeModel = 'all';
  let lbIndex = 0;
  // The lightbox can show either the main grid (`filtered`) or a collection's
  // images. lbSource is whichever list is currently being viewed.
  let lbSource = [];
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

  // Collections store: server-side at /api/image-bank/collections, mirroring the
  // favorites store (JSON in contents/ready/, project-relative paths). In-memory
  // this is a {name: [paths]} map. Collections are named groupings of favorites:
  // the "Add to collection" action is only offered in the Favorites view.
  let collections = {};
  let collModalName = null;  // name of the collection open in the view modal

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
  const lbPos      = document.getElementById('ib-lb-pos');
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
  const selDownload= document.getElementById('ib-sel-download') || document.createElement('button');
  const selArchive = document.getElementById('ib-sel-archive') || document.createElement('button');
  const selClear   = document.getElementById('ib-sel-clear');
  const selCollBtn = document.getElementById('ib-sel-collection') || document.createElement('button');

  // Collection picker modal (choose existing / create new)
  const collpick         = document.getElementById('ib-collpick');
  const collpickBack     = document.getElementById('ib-collpick-backdrop');
  const collpickClose    = document.getElementById('ib-collpick-close');
  const collpickHead     = document.getElementById('ib-collpick-head');
  const collpickExisting = document.getElementById('ib-collpick-existing');
  const collpickInput    = document.getElementById('ib-collpick-input');
  const collpickCreate   = document.getElementById('ib-collpick-create');

  // Collection view modal (all images + per-image remove)
  const collModal       = document.getElementById('ib-collmodal');
  const collModalBack   = document.getElementById('ib-collmodal-backdrop');
  const collModalClose  = document.getElementById('ib-collmodal-close');
  const collModalTitle  = document.getElementById('ib-collmodal-title');
  const collModalTitleIn= document.getElementById('ib-collmodal-title-input');
  const collModalCount  = document.getElementById('ib-collmodal-count');
  const collModalGrid   = document.getElementById('ib-collmodal-grid');
  const collModalAdd    = document.getElementById('ib-collmodal-add');
  const collModalRename = document.getElementById('ib-collmodal-rename');
  const collModalCopy   = document.getElementById('ib-collmodal-copy');
  const collModalDelete = document.getElementById('ib-collmodal-delete');

  // Add-images picker (favorites not yet in the open collection)
  const cellAdd        = document.getElementById('ib-celladd');
  const cellAddBack    = document.getElementById('ib-celladd-backdrop');
  const cellAddClose   = document.getElementById('ib-celladd-close');
  const cellAddTitle   = document.getElementById('ib-celladd-title');
  const cellAddConfirm = document.getElementById('ib-celladd-confirm');
  const cellAddGrid    = document.getElementById('ib-celladd-grid');

  let dragSrcIdx = null;        // index of the thumb being dragged in the modal
  let cellAddSel = new Set();   // paths selected in the add-images picker

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

  // -- Collections helpers -----------------------------------------------------

  // Build the cached-thumb URL for a project-relative path (same endpoint the
  // grid uses). Falls back to the full image on error at the call site.
  function thumbUrl(path, w) {
    return '/api/thumb/' + path + '?w=' + (w || 240);
  }

  async function loadCollectionsFromServer() {
    try {
      const r = await fetch('/api/image-bank/collections');
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
    // "Add to collection" is favorites-scoped: only when viewing the Favorites pill.
    selCollBtn.classList.toggle('hidden', !(n > 0 && activeType === 'favorites'));
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

  // Bulk download -- POST selected paths, get a single ZIP blob back, save it.
  // Read-only on the server (no archive/delete), so no two-click confirm needed.
  async function downloadSelected() {
    if (selected.size === 0) return;
    const paths = [...selected].map(urlToPath);
    const label = selDownload.dataset.label || selDownload.textContent;
    selDownload.dataset.label = label;
    selDownload.disabled = true;
    selDownload.textContent = `Zipping ${paths.length}…`;
    try {
      const r = await fetch('/api/image-bank/download-zip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paths }),
      });
      if (!r.ok) throw new Error('zip failed');
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dubery-images-${paths.length}.zip`;
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
        loadCollectionsFromServer(),
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
    // Collections view renders from the collections map, not the image list.
    if (activeType === 'collections') {
      filtered = [];
      renderCollections();
      const n = Object.keys(collections).length;
      count.textContent = `${n} collection${n !== 1 ? 's' : ''}`;
      modelGrp.style.display = 'none';
      copyPaths.classList.add('hidden');
      selCollBtn.classList.add('hidden');  // not a favorites view
      return;
    }
    const q = search.value.trim().toLowerCase();
    filtered = allImages.filter(img => {
      if (activeType === 'favorites') {
        if (!favorites.has(img.url)) return false;
        // Favorites view still honors the filename search box.
        if (q && !img.filename.toLowerCase().includes(q)) return false;
        return true;
      }
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

    // Keep the favorites-scoped "Add to collection" button in sync when the
    // active filter changes while a selection is still live.
    selCollBtn.classList.toggle('hidden', !(selected.size > 0 && activeType === 'favorites'));
  }

  function renderGrid() {
    loading.style.display = 'none';
    // Leaving collections view -- drop any collection cards/sections + the class.
    grid.classList.remove('coll-mode');
    grid.querySelectorAll('.ib-thumb, .ib-coll-card, .ib-coll-series').forEach(el => el.remove());

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

  // -- Collections view (fanned-deck cards) ------------------------------------

  // Attach a thumb-endpoint src with a full-image fallback (mirrors the grid).
  function setThumbWithFallback(imgEl, path) {
    imgEl.src = thumbUrl(path, 240);
    imgEl.addEventListener('error', function once() {
      imgEl.removeEventListener('error', once);
      imgEl.src = pathToUrl(path);
    }, { once: true });
  }

  // Series = the text before the first dash ("Outback - Blue" -> "Outback").
  // Collections without a dash fall into an "Other" group.
  function collectionSeries(name) {
    const parts = name.split(/\s*[-–—]\s*/);
    return (parts.length > 1 && parts[0].trim()) ? parts[0].trim() : 'Other';
  }

  function buildCollCard(name) {
    const paths = collections[name] || [];
    const card = document.createElement('div');
    card.className = 'ib-coll-card';
    card.addEventListener('click', () => openCollModal(name));

    // Fanned deck -- first 3 paths; front (f1) = cover = first image. Append
    // back -> front so the cover stacks on top via DOM order.
    const deck = document.createElement('div');
    deck.className = 'ib-coll-deck';
    const fan = paths.slice(0, 3);  // [cover, second, third]
    [
      { cls: 'f3', path: fan[2] },  // back
      { cls: 'f2', path: fan[1] },  // middle
      { cls: 'f1', path: fan[0] },  // front / cover
    ].forEach(o => {
      if (!o.path) return;
      const im = document.createElement('img');
      im.className = 'ib-coll-fan ' + o.cls;
      im.loading = 'lazy';
      im.decoding = 'async';
      im.alt = '';
      setThumbWithFallback(im, o.path);
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
    sub.textContent = `${paths.length} image${paths.length !== 1 ? 's' : ''}`;

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
      empty.textContent = 'No collections yet. Open the ♥ Favorites pill, select images, then "Add to collection".';
      grid.appendChild(empty);
      return;
    }

    // Group collection names by series, preserving first-seen series order.
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

  // -- Collection picker (Add to collection) -----------------------------------

  function openCollPick() {
    if (selected.size === 0) return;
    const n = selected.size;
    collpickHead.textContent = `Add ${n} image${n !== 1 ? 's' : ''} to collection`;
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
      const r = await fetch('/api/image-bank/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, paths, action: 'add' }),
      });
      const d = await r.json();
      if (!d.ok) throw new Error(d.error || 'failed');
      collections = d.collections || collections;
      // Confirm in-place, then close + clear the selection.
      collpickHead.textContent = `Added ${paths.length} to "${name}"`;
      setTimeout(() => { closeCollPick(); clearSelection(); }, 800);
    } catch (e) {
      collpickHead.textContent = 'Add failed — try again';
    }
  }

  // -- Collection view modal (per-image remove) --------------------------------

  function openCollModal(name) {
    collModalName = name;
    cancelRename();    // ensure title (not the rename input) is showing
    resetCollDel();    // disarm any pending delete
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
    collModalCount.textContent = `${paths.length} image${paths.length !== 1 ? 's' : ''}`;
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

      // Native drag-to-reorder. The cell owns the drag; the img is not draggable
      // so it can't start its own ghost drag.
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

      // Click (not a drag, not the × button) opens the image in the lightbox.
      cell.addEventListener('click', () => openLightboxFromCollection(idx));

      const im = document.createElement('img');
      im.loading = 'lazy';
      im.decoding = 'async';
      im.draggable = false;
      im.alt = path.split('/').pop();
      setThumbWithFallback(im, path);
      const rm = document.createElement('button');
      rm.className = 'ib-collmodal-remove';
      rm.textContent = '×';
      rm.title = 'Remove from collection';
      rm.addEventListener('click', e => { e.stopPropagation(); removeFromCollection(path); });
      cell.appendChild(im);
      cell.appendChild(rm);
      collModalGrid.appendChild(cell);
    });
  }

  // Removing only edits collections.json -- never touches favorites.json, the
  // -fav mirror copy, or the underlying file. The image stays favorited + on disk.
  async function removeFromCollection(path) {
    if (!collModalName) return;
    const name = collModalName;
    try {
      const r = await fetch('/api/image-bank/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, paths: [path], action: 'remove' }),
      });
      const d = await r.json();
      if (!d.ok) throw new Error(d.error || 'failed');
      collections = d.collections || {};
      // Server drops a collection once empty -- close the modal if so.
      if (!collections[name]) closeCollModal();
      else renderCollModal();
      // Keep the cards behind in sync (also refreshes the count).
      if (activeType === 'collections') applyFilters();
    } catch (e) {
      // best-effort -- leave the modal as-is on failure
    }
  }

  // Reorder: move the dragged thumb to a new slot. The new order is the cover
  // order (first image = fanned-deck cover). Optimistic, then persisted.
  async function reorderCollection(from, to) {
    const cur = (collections[collModalName] || []).slice();
    if (from < 0 || from >= cur.length || to < 0 || to >= cur.length) return;
    const [moved] = cur.splice(from, 1);
    cur.splice(to, 0, moved);
    collections[collModalName] = cur;     // optimistic
    renderCollModal();
    if (activeType === 'collections') applyFilters();
    try {
      const r = await fetch('/api/image-bank/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: collModalName, paths: cur, action: 'reorder' }),
      });
      const d = await r.json();
      if (!d.ok) throw new Error(d.error || 'failed');
      collections = d.collections || collections;
    } catch (e) {
      await loadCollectionsFromServer();  // recover true order on failure
      renderCollModal();
      if (activeType === 'collections') applyFilters();
    }
  }

  // -- Rename (inline title edit) ----------------------------------------------

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
      const r = await fetch('/api/image-bank/collections', {
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
      // Surface the reason (e.g. name conflict) in the still-open input.
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

  // -- Delete collection (two-click confirm; images untouched) -----------------

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
      const r = await fetch('/api/image-bank/collections', {
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

  // -- Add-images picker (favorites not yet in the open collection) ------------

  function openCellAdd() {
    if (!collModalName) return;
    const members = new Set(collections[collModalName] || []);
    const favPaths = [...favorites].map(urlToPath).filter(p => !members.has(p));
    cellAddSel = new Set();
    cellAddTitle.textContent = `Add images to "${collModalName}"`;
    cellAddGrid.innerHTML = '';
    if (favPaths.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'ib-celladd-empty';
      empty.textContent = 'All your favorites are already in this collection. Favorite more images (♥) to add them here.';
      cellAddGrid.appendChild(empty);
    } else {
      favPaths.forEach(path => {
        const cell = document.createElement('div');
        cell.className = 'ib-celladd-thumb';
        const im = document.createElement('img');
        im.loading = 'lazy';
        im.decoding = 'async';
        im.alt = path.split('/').pop();
        setThumbWithFallback(im, path);
        const chk = document.createElement('span');
        chk.className = 'ib-celladd-check';
        chk.textContent = '';
        cell.appendChild(im);
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
      const r = await fetch('/api/image-bank/collections', {
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

  // -- Lightbox ----------------------------------------------------------------

  function syncLbFav(url) {
    const isFaved = favorites.has(url);
    lbFav.textContent = isFaved ? '♥ Unfavorite' : '♡ Favorite';
    lbFav.classList.toggle('faved', isFaved);
  }

  function openLightbox(idx) {
    lbSource = filtered;   // viewing the main grid
    lbIndex = idx;
    showLb();
    lb.classList.remove('hidden');
  }

  // Open the lightbox on a collection's images (called from the collection
  // modal). Looks up full metadata from allImages when available so the badges
  // match the grid; falls back to a minimal object otherwise.
  function openLightboxFromCollection(idx) {
    const paths = collections[collModalName] || [];
    if (!paths.length) return;
    lbSource = paths.map(p => {
      const url = pathToUrl(p);
      return allImages.find(i => i.url === url) ||
             { url, filename: p.split('/').pop(), type: '', model: null };
    });
    lbIndex = Math.max(0, Math.min(idx, lbSource.length - 1));
    showLb();
    lb.classList.remove('hidden');
  }

  function showLb() {
    const img = lbSource[lbIndex];
    if (!img) return;
    lbImg.src = img.url;
    lbImg.alt = img.filename;
    lbType.textContent = img.type;
    lbType.className = `ib-lb-type ib-badge ib-badge--${img.type}`;
    lbType.style.display = img.type ? '' : 'none';
    lbModel.textContent = img.model ? (MODEL_LABELS[img.model] || img.model) : '';
    lbModel.style.display = img.model ? '' : 'none';
    lbName.textContent = img.filename;
    lbDl.href = img.url;
    lbDl.download = img.filename;
    lbPrev.disabled = lbIndex === 0;
    lbNext.disabled = lbIndex === lbSource.length - 1;
    if (lbPos) lbPos.textContent = lbSource.length ? `${lbIndex + 1} / ${lbSource.length}` : '';
    syncLbFav(img.url);
    resetArchiveBtn();
  }

  function closeLightbox() { lb.classList.add('hidden'); resetArchiveBtn(); }

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
    const img = lbSource[lbIndex];
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

  // Collection modal management actions
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

  // Add-images picker wiring
  cellAddClose.addEventListener('click', closeCellAdd);
  cellAddBack.addEventListener('click', closeCellAdd);
  cellAddConfirm.addEventListener('click', confirmCellAdd);

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
    // The lightbox is the topmost view when open (it can open over the
    // collection modal), so it handles keys first.
    if (!lb.classList.contains('hidden')) {
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft' && lbIndex > 0) { lbIndex--; showLb(); }
      if (e.key === 'ArrowRight' && lbIndex < lbSource.length - 1) { lbIndex++; showLb(); }
      return;
    }
    // Add-images picker opens over the collection modal, so it goes next.
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
    // No overlay open -- Esc clears an active selection.
    if (e.key === 'Escape' && selected.size > 0) clearSelection();
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
