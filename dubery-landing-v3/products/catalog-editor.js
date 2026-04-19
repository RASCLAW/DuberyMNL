/* products/catalog-editor.js — edit primary + hover images, activated via ?edit
   Load after catalog.js. Waits for grid to render. */
(function () {
  if (!location.search.includes('edit')) return;

  let viewMode = 'hover'; // 'hover' | 'primary'

  function waitAndStart() {
    const grid = document.querySelector('[data-catalog-grid]');
    if (!grid || !grid.querySelector('.catalog-card')) { setTimeout(waitAndStart, 50); return; }
    setup();
  }
  waitAndStart();

  function setup() {
    injectStyles();
    wrapImages();
    buildBar();
    applyViewMode();
  }

  /* ── Styles ── */
  function injectStyles() {
    const s = document.createElement('style');
    s.id = 'catalog-editor-styles';
    s.textContent = `
      body { padding-bottom: 72px !important; }

      /* View mode overrides — toggled via JS class on body */
      body.edit-view-hover  .bs-img.hover   { opacity: 1 !important; }
      body.edit-view-hover  .bs-img.primary { opacity: 0 !important; }
      body.edit-view-primary .bs-img.primary { opacity: 1 !important; }
      body.edit-view-primary .bs-img.hover   { opacity: 0 !important; }

      /* Block card hover from interfering */
      .bs-card:hover .bs-img.primary,
      .bs-card:hover .bs-img.hover { opacity: inherit; }

      .img-edit-wrap {
        position: absolute;
        inset: 0;
        line-height: 0;
      }
      .img-edit-overlay {
        position: absolute;
        inset: 0;
        background: transparent;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: background 0.18s;
        z-index: 10;
      }
      .img-edit-label {
        color: #fff;
        font-family: system-ui, sans-serif;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 6px 12px;
        background: rgba(0,0,0,0.75);
        border-radius: 6px;
        opacity: 0;
        transition: opacity 0.18s;
        pointer-events: none;
        white-space: nowrap;
      }
      .img-edit-wrap:hover .img-edit-overlay { background: rgba(0,0,0,0.3); }
      .img-edit-wrap:hover .img-edit-label   { opacity: 1; }
      .img-edit-wrap.drag-active .img-edit-overlay { background: rgba(59,130,246,0.45); }
      .img-edit-wrap.drag-active .img-edit-label   { opacity: 1; background: #3b82f6; }

      .editor-bar {
        position: fixed;
        bottom: 0; left: 0; right: 0;
        background: #0f172a;
        color: #e2e8f0;
        padding: 0 24px;
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        z-index: 99999;
        box-shadow: 0 -2px 16px rgba(0,0,0,0.4);
        font-family: system-ui, sans-serif;
        font-size: 13px;
      }
      .editor-bar-status {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #94a3b8;
      }
      .editor-dot { width: 8px; height: 8px; background: #22c55e; border-radius: 50%; flex-shrink: 0; }
      .editor-bar-btns { display: flex; gap: 8px; }
      .ebtn {
        padding: 7px 18px;
        border-radius: 6px;
        border: none;
        cursor: pointer;
        font-size: 13px;
        font-weight: 600;
        font-family: inherit;
        transition: opacity 0.15s;
      }
      .ebtn:hover { opacity: 0.82; }
      .ebtn-save   { background: #3b82f6; color: #fff; }
      .ebtn-toggle { background: #334155; color: #e2e8f0; }
      .ebtn-exit   { background: transparent; color: #64748b; border: 1px solid #334155; }
    `;
    document.head.appendChild(s);
  }

  /* ── Wrap both primary and hover images on every card ── */
  function wrapImages() {
    document.querySelectorAll('.catalog-card').forEach(card => {
      const primary = card.querySelector('.bs-img.primary');
      const hover   = card.querySelector('.bs-img.hover');
      if (primary) wrapImage(primary, 'Replace primary');
      if (hover)   wrapImage(hover,   'Replace hover');
    });
  }

  function wrapImage(img, label) {
    const media = img.closest('.bs-media');
    if (!media) return;

    const wrap = document.createElement('div');
    wrap.className = 'img-edit-wrap';
    wrap.dataset.imgType = img.classList.contains('hover') ? 'hover' : 'primary';
    media.appendChild(wrap);

    const overlay = document.createElement('div');
    overlay.className = 'img-edit-overlay';
    const lbl = document.createElement('span');
    lbl.className = 'img-edit-label';
    lbl.textContent = label;
    overlay.appendChild(lbl);
    wrap.appendChild(overlay);

    overlay.addEventListener('click', () => pickFile(img));
    wrap.addEventListener('dragover', e => { e.preventDefault(); wrap.classList.add('drag-active'); });
    wrap.addEventListener('dragleave', e => { if (!wrap.contains(e.relatedTarget)) wrap.classList.remove('drag-active'); });
    wrap.addEventListener('drop', e => {
      e.preventDefault();
      wrap.classList.remove('drag-active');
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith('image/')) loadImageFile(file, img);
    });
  }

  /* ── Show only the overlay for the current view mode ── */
  function applyViewMode() {
    document.body.classList.remove('edit-view-hover', 'edit-view-primary');
    document.body.classList.add(`edit-view-${viewMode}`);
    document.querySelectorAll('.img-edit-wrap').forEach(wrap => {
      wrap.style.display = wrap.dataset.imgType === viewMode ? 'block' : 'none';
    });
    const btn = document.getElementById('eb-toggle');
    if (btn) btn.textContent = viewMode === 'hover' ? 'Switch to Primary' : 'Switch to Hover';
  }

  function pickFile(img) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = e => { const f = e.target.files[0]; if (f) loadImageFile(f, img); };
    input.click();
  }

  function loadImageFile(file, img) {
    const reader = new FileReader();
    reader.onload = e => { img.src = e.target.result; };
    reader.readAsDataURL(file);
  }

  /* ── Editor bar ── */
  function buildBar() {
    const bar = document.createElement('div');
    bar.className = 'editor-bar';
    bar.innerHTML = `
      <div class="editor-bar-status">
        <div class="editor-dot"></div>
        <span>Edit mode &mdash; viewing <strong id="eb-mode-label">HOVER</strong> images &mdash; click to replace &bull; drag &amp; drop</span>
      </div>
      <div class="editor-bar-btns">
        <button class="ebtn ebtn-exit"   id="eb-exit">Exit</button>
        <button class="ebtn ebtn-toggle" id="eb-toggle">Switch to Primary</button>
        <button class="ebtn ebtn-save"   id="eb-save">Save HTML</button>
      </div>
    `;
    document.body.appendChild(bar);

    document.getElementById('eb-exit').addEventListener('click', () => {
      const params = new URLSearchParams(location.search);
      params.delete('edit');
      const qs = params.toString();
      location.href = location.pathname + (qs ? '?' + qs : '');
    });

    document.getElementById('eb-toggle').addEventListener('click', () => {
      viewMode = viewMode === 'hover' ? 'primary' : 'hover';
      document.getElementById('eb-mode-label').textContent = viewMode.toUpperCase();
      applyViewMode();
    });

    document.getElementById('eb-save').addEventListener('click', saveHTML);
  }

  /* ── Save HTML ── */
  function saveHTML() {
    const clone = document.documentElement.cloneNode(true);

    clone.querySelector('#catalog-editor-styles')?.remove();
    clone.querySelector('.editor-bar')?.remove();
    clone.classList.remove('edit-view-hover', 'edit-view-primary');

    // Remove edit overlays, restore normal opacity
    clone.querySelectorAll('.img-edit-wrap').forEach(w => w.remove());
    clone.querySelectorAll('.bs-img.primary').forEach(img => img.style.removeProperty('opacity'));
    clone.querySelectorAll('.bs-img.hover').forEach(img => img.style.removeProperty('opacity'));

    const html = '<!DOCTYPE html>\n' + clone.outerHTML;
    const blob = new Blob([html], { type: 'text/html' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'catalog-edit.html';
    a.click();
    URL.revokeObjectURL(a.href);
  }

})();
