/* products/item-editor.js — visual edit mode for PDP, activated via ?edit in URL
   Same pattern as editor.js on index.html. Waits for item.js hydration. */
(function () {
  if (!location.search.includes('edit')) return;

  function waitAndStart() {
    const root = document.querySelector('[data-pdp-root]');
    if (!root || root.hidden) { setTimeout(waitAndStart, 50); return; }
    setup();
  }
  waitAndStart();

  function setup() {
    injectStyles();
    wrapGalleryImages();
    rewireThumbClicks();
    addGalleryAddButton();
    makeFieldsEditable();
    buildBar();
  }

  /* ── Styles ── */
  function injectStyles() {
    const s = document.createElement('style');
    s.id = 'pdp-editor-styles';
    s.textContent = `
      body { padding-bottom: 72px !important; }

      .img-edit-wrap {
        position: relative;
        display: block;
        line-height: 0;
        width: 100%;
        height: 100%;
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
        z-index: 5;
      }
      .img-edit-label {
        color: #fff;
        font-family: system-ui, sans-serif;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 7px 14px;
        background: rgba(0,0,0,0.75);
        border-radius: 6px;
        opacity: 0;
        transition: opacity 0.18s;
        pointer-events: none;
        white-space: nowrap;
      }
      .img-edit-wrap:hover .img-edit-overlay { background: rgba(0,0,0,0.28); }
      .img-edit-wrap:hover .img-edit-label   { opacity: 1; }
      .img-edit-wrap.drag-active .img-edit-overlay { background: rgba(59,130,246,0.45); }
      .img-edit-wrap.drag-active .img-edit-label   { opacity: 1; background: #3b82f6; }

      .pdp-thumb-add {
        display: flex !important;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        font-weight: 300;
        color: #94a3b8;
        border: 2px dashed #d1d5db !important;
        background: transparent;
        cursor: pointer;
        border-radius: 6px;
        transition: border-color 0.15s, color 0.15s;
        min-width: 60px;
      }
      .pdp-thumb-add:hover { border-color: #3b82f6 !important; color: #3b82f6; }

      .editable-text {
        cursor: text;
        border-radius: 3px;
        transition: outline 0.1s;
      }
      .editable-text:hover {
        outline: 2px dashed rgba(59,130,246,0.55);
        outline-offset: 3px;
      }
      .editable-text[contenteditable="true"] {
        outline: 2px solid #3b82f6;
        outline-offset: 3px;
        background: rgba(59,130,246,0.05);
      }

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
      .ebtn-save { background: #3b82f6; color: #fff; }
      .ebtn-exit { background: transparent; color: #64748b; border: 1px solid #334155; }
    `;
    document.head.appendChild(s);
  }

  /* ── Image wrap helper ── */
  function wrapImage(img) {
    if (img.closest('.img-edit-wrap')) return;
    const wrap = document.createElement('div');
    wrap.className = 'img-edit-wrap';
    img.parentNode.insertBefore(wrap, img);
    wrap.appendChild(img);

    const overlay = document.createElement('div');
    overlay.className = 'img-edit-overlay';
    const label = document.createElement('span');
    label.className = 'img-edit-label';
    label.textContent = 'Click or drop to replace';
    overlay.appendChild(label);
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

  function wrapGalleryImages() {
    document.querySelectorAll('.pdp-gallery img').forEach(wrapImage);
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

  /* ── Re-wire thumb clicks to use current img src ── */
  function rewireThumbClicks() {
    const mainImg = document.querySelector('[data-field="gallery-main"]');
    if (!mainImg) return;
    document.querySelectorAll('.pdp-thumb:not(.pdp-thumb-add)').forEach(btn => {
      btn.addEventListener('click', () => {
        const thumbImg = btn.querySelector('img');
        if (thumbImg) mainImg.src = thumbImg.src;
        document.querySelectorAll('.pdp-thumb').forEach(t => t.classList.remove('is-active'));
        btn.classList.add('is-active');
      });
    });
  }

  /* ── Add-image button ── */
  function addGalleryAddButton() {
    const thumbsWrap = document.querySelector('[data-field="gallery-thumbs"]');
    const mainImg    = document.querySelector('[data-field="gallery-main"]');
    if (!thumbsWrap) return;

    const addBtn = document.createElement('button');
    addBtn.type = 'button';
    addBtn.className = 'pdp-thumb pdp-thumb-add';
    addBtn.title = 'Add image';
    addBtn.textContent = '+';
    thumbsWrap.appendChild(addBtn);

    addBtn.addEventListener('click', () => {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.multiple = true;
      input.onchange = e => {
        Array.from(e.target.files).forEach(file => {
          if (file.type.startsWith('image/')) addThumbFromFile(file, thumbsWrap, mainImg, addBtn);
        });
      };
      input.click();
    });
  }

  function addThumbFromFile(file, thumbsWrap, mainImg, addBtn) {
    const reader = new FileReader();
    reader.onload = e => {
      const dataUrl = e.target.result;
      const idx = thumbsWrap.querySelectorAll('.pdp-thumb:not(.pdp-thumb-add)').length;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pdp-thumb';
      btn.dataset.galleryIndex = idx;

      const img = document.createElement('img');
      img.src = dataUrl;
      img.alt = '';
      img.loading = 'lazy';
      btn.appendChild(img);
      thumbsWrap.insertBefore(btn, addBtn);

      btn.addEventListener('click', () => {
        if (mainImg) mainImg.src = dataUrl;
        thumbsWrap.querySelectorAll('.pdp-thumb').forEach(t => t.classList.remove('is-active'));
        btn.classList.add('is-active');
      });

      wrapImage(img);

      if (mainImg) {
        mainImg.src = dataUrl;
        thumbsWrap.querySelectorAll('.pdp-thumb').forEach(t => t.classList.remove('is-active'));
        btn.classList.add('is-active');
      }
    };
    reader.readAsDataURL(file);
  }

  /* ── Editable text fields ── */
  const EDITABLE_FIELDS = ['series-eyebrow', 'colorway', 'copy', 'frame', 'lens'];

  function makeFieldsEditable() {
    EDITABLE_FIELDS.forEach(field => {
      const el = document.querySelector(`[data-field="${field}"]`);
      if (!el) return;
      el.classList.add('editable-text');
      el.addEventListener('click', e => {
        e.preventDefault();
        e.stopPropagation();
        el.contentEditable = 'true';
        el.focus();
        const range = document.createRange();
        range.selectNodeContents(el);
        range.collapse(false);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
      });
      el.addEventListener('blur', () => { el.contentEditable = 'false'; });
      el.addEventListener('keydown', e => { if (e.key === 'Escape') el.blur(); });
    });
  }

  /* ── Editor bar ── */
  function buildBar() {
    const bar = document.createElement('div');
    bar.className = 'editor-bar';
    bar.innerHTML = `
      <div class="editor-bar-status">
        <div class="editor-dot"></div>
        <span>Edit mode &mdash; click images to replace &bull; drag images onto them &bull; click + to add &bull; click text to edit</span>
      </div>
      <div class="editor-bar-btns">
        <button class="ebtn ebtn-exit" id="eb-exit">Exit</button>
        <button class="ebtn ebtn-save" id="eb-save">Save HTML</button>
      </div>
    `;
    document.body.appendChild(bar);

    document.getElementById('eb-exit').addEventListener('click', () => {
      const params = new URLSearchParams(location.search);
      params.delete('edit');
      const qs = params.toString();
      location.href = location.pathname + (qs ? '?' + qs : '');
    });

    document.getElementById('eb-save').addEventListener('click', saveHTML);
  }

  /* ── Save HTML ── */
  function saveHTML() {
    const clone = document.documentElement.cloneNode(true);

    clone.querySelector('#pdp-editor-styles')?.remove();
    clone.querySelector('.editor-bar')?.remove();
    clone.querySelector('.pdp-thumb-add')?.remove();

    clone.querySelectorAll('.img-edit-wrap').forEach(wrap => {
      const img = wrap.querySelector('img');
      wrap.querySelector('.img-edit-overlay')?.remove();
      wrap.replaceWith(img);
    });

    clone.querySelectorAll('[contenteditable]').forEach(el => el.removeAttribute('contenteditable'));
    clone.querySelectorAll('.editable-text').forEach(el => el.classList.remove('editable-text'));

    const html = '<!DOCTYPE html>\n' + clone.outerHTML;
    const blob = new Blob([html], { type: 'text/html' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    const slug = new URLSearchParams(location.search).get('slug') || 'product';
    a.download = `item-${slug}.html`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

})();
