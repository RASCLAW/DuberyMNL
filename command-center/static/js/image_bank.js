/* Image Bank tab */
(function () {
  let allImages = [];
  let filtered = [];
  let activeType = 'all';
  let activeModel = 'all';
  let lbIndex = 0;

  const grid     = document.getElementById('ib-grid');
  const loading  = document.getElementById('ib-loading');
  const count    = document.getElementById('ib-count');
  const search   = document.getElementById('ib-search');
  const typeGrp  = document.getElementById('ib-type-filters');
  const modelGrp = document.getElementById('ib-model-filters');
  const lb       = document.getElementById('ib-lightbox');
  const lbImg    = document.getElementById('ib-lb-img');
  const lbType   = document.getElementById('ib-lb-type');
  const lbModel  = document.getElementById('ib-lb-model');
  const lbName   = document.getElementById('ib-lb-name');
  const lbDl     = document.getElementById('ib-lb-dl');
  const lbCopy   = document.getElementById('ib-lb-copy');
  const lbClose  = document.getElementById('ib-lb-close');
  const lbPrev   = document.getElementById('ib-lb-prev');
  const lbNext   = document.getElementById('ib-lb-next');
  const lbBack   = document.getElementById('ib-lb-backdrop');

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

  async function init() {
    // Only run when this tab is visible
    const tabEl = document.querySelector('.tab[data-tab="image-bank"]');
    if (!tabEl) return;
    const observer = new MutationObserver(() => {
      if (tabEl.classList.contains('active')) {
        load();
      }
    });
    observer.observe(tabEl, { attributes: true, attributeFilter: ['class'] });
    // Also load immediately if already active
    if (tabEl.classList.contains('active')) load();
  }

  async function load() {
    loading.style.display = '';
    grid.querySelectorAll('.ib-thumb, .ib-empty').forEach(el => el.remove());
    count.textContent = '—';
    try {
      const res = await fetch('/api/image-bank');
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
      if (activeType !== 'all' && img.type !== activeType) return false;
      if (activeModel !== 'all' && img.model !== activeModel) return false;
      if (q && !img.filename.toLowerCase().includes(q)) return false;
      return true;
    });
    renderGrid();
    count.textContent = `${filtered.length} image${filtered.length !== 1 ? 's' : ''}`;
    // Show model filters only for person/product
    modelGrp.style.display = (activeType === 'brand' || activeType === 'all') && activeType === 'brand'
      ? 'none'
      : (activeType === 'all' || activeType === 'brand') ? 'none' : 'flex';
    if (activeType !== 'brand' && activeType !== 'all') modelGrp.style.display = 'flex';
  }

  function renderGrid() {
    // Clear old items (keep loading div hidden)
    loading.style.display = 'none';
    // Remove old thumbs
    grid.querySelectorAll('.ib-thumb').forEach(el => el.remove());

    if (filtered.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'ib-empty';
      empty.textContent = 'No images match.';
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
      imgEl.src = img.url;
      imgEl.alt = img.filename;

      const badge = document.createElement('span');
      badge.className = `ib-badge ib-badge--${img.type}`;
      badge.textContent = img.type === 'brand' ? 'brand' : (MODEL_LABELS[img.model] || img.model || '');

      div.appendChild(imgEl);
      div.appendChild(badge);
      div.addEventListener('click', () => openLightbox(idx));
      grid.appendChild(div);
    });
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

  document.addEventListener('keydown', e => {
    if (lb.classList.contains('hidden')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft' && lbIndex > 0) { lbIndex--; showLb(); }
    if (e.key === 'ArrowRight' && lbIndex < filtered.length - 1) { lbIndex++; showLb(); }
  });

  // Type filter chips
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
