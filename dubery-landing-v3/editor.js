(function () {
  if (!location.search.includes('edit')) return;

  /* ── Styles ── */
  const style = document.createElement('style');
  style.id = 'editor-styles';
  style.textContent = `
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
    .editor-dot {
      width: 8px; height: 8px;
      background: #22c55e;
      border-radius: 50%;
      flex-shrink: 0;
    }
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
  document.head.appendChild(style);

  /* ── Wrap every image ── */
  document.querySelectorAll('img').forEach(img => {
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

    // Click → file picker
    overlay.addEventListener('click', () => pickFile(img));

    // Drag & drop
    wrap.addEventListener('dragover', e => { e.preventDefault(); wrap.classList.add('drag-active'); });
    wrap.addEventListener('dragleave', e => { if (!wrap.contains(e.relatedTarget)) wrap.classList.remove('drag-active'); });
    wrap.addEventListener('drop', e => {
      e.preventDefault();
      wrap.classList.remove('drag-active');
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith('image/')) loadImage(file, img);
    });
  });

  function pickFile(img) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = e => { const f = e.target.files[0]; if (f) loadImage(f, img); };
    input.click();
  }

  function loadImage(file, img) {
    const reader = new FileReader();
    reader.onload = e => { img.src = e.target.result; };
    reader.readAsDataURL(file);
  }

  /* ── Make text editable ── */
  const TEXT_SELECTORS = [
    'main h1', 'main h2', 'main h3',
    'main .eyebrow', 'main .lede', 'main .hero-meta',
    'main .series-label', 'main .series-sub',
    'main .bs-title', 'main .bs-price',
    'main .bs-stars', 'main .bs-count',
    'main .social-tag',
    '.proof-copy p', '.story-copy p', '.art-copy p',
    '.section-cta p', '.footer-tag'
  ].join(',');

  const SKIP = ['.bs-filters', '.bs-arrows', '.nav-links', '.trust-strip', '.bs-swatches'];

  document.querySelectorAll(TEXT_SELECTORS).forEach(el => {
    if (SKIP.some(s => el.closest(s))) return;
    if (!el.textContent.trim()) return;

    el.classList.add('editable-text');

    el.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      el.contentEditable = 'true';
      el.focus();
      // put cursor at end
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

  /* ── Editor bar ── */
  const bar = document.createElement('div');
  bar.className = 'editor-bar';
  bar.innerHTML = `
    <div class="editor-bar-status">
      <div class="editor-dot"></div>
      <span>Edit mode &mdash; click images to replace &bull; drag images onto them &bull; click text to edit</span>
    </div>
    <div class="editor-bar-btns">
      <button class="ebtn ebtn-exit" id="eb-exit">Exit</button>
      <button class="ebtn ebtn-save" id="eb-save">Save HTML</button>
    </div>
  `;
  document.body.appendChild(bar);

  document.getElementById('eb-exit').addEventListener('click', () => {
    location.href = location.pathname;
  });

  document.getElementById('eb-save').addEventListener('click', exportHTML);

  /* ── Export ── */
  function exportHTML() {
    const clone = document.documentElement.cloneNode(true);

    // Remove editor UI
    clone.querySelector('#editor-styles')?.remove();
    clone.querySelector('.editor-bar')?.remove();

    // Unwrap img-edit-wrap → restore bare <img>
    clone.querySelectorAll('.img-edit-wrap').forEach(wrap => {
      const img = wrap.querySelector('img');
      wrap.querySelector('.img-edit-overlay')?.remove();
      wrap.replaceWith(img);
    });

    // Clean editor attributes and classes
    clone.querySelectorAll('[contenteditable]').forEach(el => el.removeAttribute('contenteditable'));
    clone.querySelectorAll('.editable-text').forEach(el => el.classList.remove('editable-text'));

    const html = '<!DOCTYPE html>\n' + clone.outerHTML;
    const blob = new Blob([html], { type: 'text/html' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'index.html';
    a.click();
    URL.revokeObjectURL(a.href);
  }

})();
