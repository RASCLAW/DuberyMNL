/* DuberyMNL Visual Editor v3 — Direct Manipulation
   ?edit to activate. Click=select, Drag=move, Corner handles=resize.
   Ctrl+Click=multi-select. Ctrl+Z=undo. E=toggle toolbar. */

(() => {
  'use strict';
  if (!location.search.includes('edit')) return;

  // ── State ──
  let selection = [];
  let sketchMode = false;
  let isDrawing = false;
  let sketchColor = '#E8110F';
  let sketchWidth = 3;
  let changes = {};
  let undoStack = [];
  let isDragging = false;
  let isResizing = false;
  let dragStart = { x: 0, y: 0 };
  let dragOffsets = {}; // per-element start positions
  let resizeEl = null;
  let resizeHandle = '';
  let resizeStart = { x: 0, y: 0, w: 0, h: 0, fs: 0 };

  // ── Styles ──
  const style = document.createElement('style');
  style.textContent = `
    .ve-selected { outline: 2px solid #E8110F !important; outline-offset: 2px; cursor: move; -webkit-user-select: none !important; user-select: none !important; -webkit-user-drag: none !important; }
    .ve-hover { outline: 1px dashed rgba(232,17,15,0.5) !important; outline-offset: 2px; }
    .ve-handle {
      position: fixed; width: 14px; height: 14px; background: #E8110F;
      border: 2px solid #fff; border-radius: 2px; z-index: 100001;
      pointer-events: auto; touch-action: none;
    }
    .ve-handle-tl, .ve-handle-br { cursor: nwse-resize; }
    .ve-handle-tr, .ve-handle-bl { cursor: nesw-resize; }
    .ve-handle-t, .ve-handle-b { cursor: ns-resize; width: 20px; height: 8px; }
    .ve-handle-l, .ve-handle-r { cursor: ew-resize; width: 8px; height: 20px; }
    .ve-size-label {
      position: fixed; z-index: 100001; background: #E8110F; color: #fff;
      font: 600 10px/1 'Inter', system-ui, sans-serif; padding: 3px 6px;
      border-radius: 3px; pointer-events: none; white-space: nowrap;
    }

    .ve-toolbar {
      position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%);
      z-index: 100000; display: flex; align-items: center; gap: 6px;
      background: rgba(20,20,20,0.92); backdrop-filter: blur(12px);
      border: 1px solid #444; border-radius: 10px; padding: 8px 14px;
      font-family: 'Inter', system-ui, sans-serif; font-size: 12px; color: #eee;
    }
    .ve-toolbar.ve-hidden { display: none; }
    .ve-toolbar button {
      background: #333; color: #eee; border: 1px solid #555; padding: 6px 10px;
      border-radius: 5px; cursor: pointer; font-size: 11px; font-weight: 600;
      transition: background 0.15s;
    }
    .ve-toolbar button:hover { background: #555; }
    .ve-toolbar button:disabled { opacity: 0.3; cursor: default; }
    .ve-toolbar button.ve-active { background: #E8110F; border-color: #E8110F; }
    .ve-toolbar input[type="color"] { width: 28px; height: 28px; border: 2px solid #555; border-radius: 6px; background: none; cursor: pointer; padding: 0; }
    .ve-toolbar .ve-sep { width: 1px; height: 20px; background: #444; }
    .ve-tb-label { font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 0.05em; }

    .ve-sketch-canvas { position: fixed; inset: 0; z-index: 99998; cursor: crosshair; }
    .ve-toggle-btn {
      position: fixed; bottom: 16px; right: 16px; z-index: 100002;
      background: #E8110F; color: #fff; border: none; width: 36px; height: 36px;
      border-radius: 50%; font-size: 14px; font-weight: 700; cursor: pointer;
      box-shadow: 0 2px 12px rgba(0,0,0,0.4);
    }
    .ve-export-toast {
      position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
      z-index: 100003; background: #1a1a1a; color: #0f0; border: 1px solid #333;
      border-radius: 8px; padding: 12px 20px; font-family: monospace; font-size: 11px;
      max-width: 500px; max-height: 300px; overflow-y: auto; white-space: pre-wrap;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5); display: none;
    }
  `;
  document.head.appendChild(style);

  // ── Toolbar ──
  const toolbar = document.createElement('div');
  toolbar.className = 've-toolbar';
  toolbar.innerHTML = `
    <span class="ve-tb-label" id="ve-info">Click to select</span>
    <div class="ve-sep"></div>
    <span class="ve-tb-label">Color</span>
    <input type="color" id="ve-color" value="#ffffff" title="Text color">
    <input type="color" id="ve-bg" value="#000000" title="Background color">
    <div class="ve-sep"></div>
    <button id="ve-sketch-toggle" title="Pen tool">Pen</button>
    <input type="color" id="ve-sk-color" value="#E8110F" title="Pen color" style="width:24px;height:24px;">
    <div class="ve-sep"></div>
    <button id="ve-add-text" title="Add text element">+ Text</button>
    <button id="ve-add-img" title="Add image">+ Image</button>
    <input type="file" id="ve-file-input" accept="image/*" style="display:none">
    <div class="ve-sep"></div>
    <button id="ve-undo" disabled title="Undo (Ctrl+Z)">Undo <span id="ve-undo-count"></span></button>
    <button id="ve-export" title="Export CSS">Export</button>
  `;
  document.body.appendChild(toolbar);

  const toggleBtn = document.createElement('button');
  toggleBtn.className = 've-toggle-btn';
  toggleBtn.textContent = 'E';
  document.body.appendChild(toggleBtn);

  const exportToast = document.createElement('div');
  exportToast.className = 've-export-toast';
  document.body.appendChild(exportToast);

  let toolbarVisible = true;
  const toggleToolbar = () => {
    toolbarVisible = !toolbarVisible;
    toolbar.classList.toggle('ve-hidden', !toolbarVisible);
  };
  toggleBtn.addEventListener('click', toggleToolbar);

  // ── Sketch canvas ──
  const sketchCanvas = document.createElement('canvas');
  sketchCanvas.className = 've-sketch-canvas';
  sketchCanvas.style.display = 'none';
  document.body.appendChild(sketchCanvas);
  const skCtx = sketchCanvas.getContext('2d');
  const resizeSketch = () => { sketchCanvas.width = window.innerWidth; sketchCanvas.height = window.innerHeight; };
  resizeSketch();
  window.addEventListener('resize', resizeSketch);

  // ── Handles container ──
  const handlesWrap = document.createElement('div');
  handlesWrap.style.cssText = 'position:fixed;inset:0;z-index:100001;pointer-events:none;';
  document.body.appendChild(handlesWrap);
  // Stop handle clicks from reaching the document select handler
  handlesWrap.addEventListener('click', (e) => { e.stopPropagation(); }, true);

  const sizeLabel = document.createElement('div');
  sizeLabel.className = 've-size-label';
  sizeLabel.style.display = 'none';
  document.body.appendChild(sizeLabel);

  // ── Helpers ──
  const $ = (id) => document.getElementById(id);
  const rgbToHex = (str) => {
    const m = str.match(/\d+/g);
    if (!m || m.length < 3) return '#000000';
    return '#' + m.slice(0, 3).map(n => parseInt(n).toString(16).padStart(2, '0')).join('');
  };
  const getSelector = (el) => {
    if (el.id) return '#' + el.id;
    if (el.className && typeof el.className === 'string') {
      const cls = el.className.split(' ').filter(c => !c.startsWith('ve-') && c !== 've-selected')[0];
      if (cls) return '.' + cls;
    }
    return el.tagName.toLowerCase();
  };
  const forceStyle = (el, prop, value) => { el.style.setProperty(prop, value, 'important'); };
  const recordChange = (el, prop, value) => {
    const sel = getSelector(el);
    if (!changes[sel]) changes[sel] = {};
    changes[sel][prop] = value;
  };
  const isEditorEl = (el) => {
    return toolbar.contains(el) || toggleBtn.contains(el) || handlesWrap.contains(el) || el === sketchCanvas || el === exportToast;
  };

  // ── Undo ──
  const pushUndoBatch = (elements, prop) => {
    const batch = elements.map(el => ({
      el, prop,
      oldValue: el.style.getPropertyValue(prop) || ''
    }));
    undoStack.push(batch);
    updateUndoUI();
  };
  const doUndo = () => {
    if (undoStack.length === 0) return;
    const entry = undoStack.pop();
    if (entry.type === 'sketch') {
      skCtx.putImageData(entry.snapshot, 0, 0);
      updateUndoUI();
      return;
    }
    const items = Array.isArray(entry) ? entry : [entry];
    items.forEach(({ el, prop, oldValue }) => {
      if (oldValue) forceStyle(el, prop, oldValue);
      else el.style.removeProperty(prop);
    });
    updateUndoUI();
    updateHandles();
  };
  const updateUndoUI = () => {
    $('ve-undo').disabled = undoStack.length === 0;
    $('ve-undo-count').textContent = undoStack.length > 0 ? `(${undoStack.length})` : '';
  };
  $('ve-undo').addEventListener('click', doUndo);

  // ── Handles ──
  const updateHandles = () => {
    handlesWrap.innerHTML = '';
    sizeLabel.style.display = 'none';
    if (selection.length === 0) return;

    selection.forEach(el => {
      const rect = el.getBoundingClientRect();
      const mx = rect.left + rect.width / 2;
      const my = rect.top + rect.height / 2;
      const handles = [
        // Corners
        { cls: 've-handle-tl', x: rect.left - 7, y: rect.top - 7 },
        { cls: 've-handle-tr', x: rect.right - 7, y: rect.top - 7 },
        { cls: 've-handle-bl', x: rect.left - 7, y: rect.bottom - 7 },
        { cls: 've-handle-br', x: rect.right - 7, y: rect.bottom - 7 },
        // Edges
        { cls: 've-handle-t', x: mx - 10, y: rect.top - 4 },
        { cls: 've-handle-b', x: mx - 10, y: rect.bottom - 4 },
        { cls: 've-handle-l', x: rect.left - 4, y: my - 10 },
        { cls: 've-handle-r', x: rect.right - 4, y: my - 10 },
      ];
      handles.forEach(({ cls, x, y }) => {
        const h = document.createElement('div');
        h.className = 've-handle ' + cls;
        h.style.left = x + 'px';
        h.style.top = y + 'px';
        h.dataset.handle = cls.replace('ve-handle-', '');
        h.dataset.elSel = getSelector(el);
        h._targetEl = el;
        handlesWrap.appendChild(h);
      });
    });
  };

  // Update handles on scroll/resize
  const rafUpdateHandles = () => { if (selection.length > 0) updateHandles(); };
  window.addEventListener('scroll', rafUpdateHandles, { passive: true });
  window.addEventListener('resize', rafUpdateHandles);

  // ── Selection ──
  const addToSelection = (el) => {
    if (selection.includes(el)) return;
    selection.push(el);
    el.classList.add('ve-selected');
    updateHandles();
    updateInfo();
  };
  const clearSelection = () => {
    selection.forEach(el => el.classList.remove('ve-selected'));
    selection = [];
    handlesWrap.innerHTML = '';
    sizeLabel.style.display = 'none';
    updateInfo();
  };
  const updateInfo = () => {
    if (selection.length === 0) {
      $('ve-info').textContent = 'Click to select';
    } else if (selection.length === 1) {
      const el = selection[0];
      let info = getSelector(el);
      // Show file path for images
      if (el.tagName === 'IMG' && el._filePath) {
        info += ' | ' + el._filePath;
      } else if (el.tagName === 'IMG' && el.src) {
        // Show src basename
        const src = el.getAttribute('src') || el.src;
        info += ' | ' + (src.startsWith('data:') ? '(uploaded)' : src.split('/').pop());
      }
      $('ve-info').textContent = info;
    } else {
      $('ve-info').textContent = selection.length + ' linked';
    }
  };

  // ── Block all link navigation in edit mode ──
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (link && !isEditorEl(e.target)) {
      e.preventDefault();
      e.stopPropagation();
    }
  }, true);

  // ── Hover ──
  let hovered = null;
  document.addEventListener('mouseover', (e) => {
    if (sketchMode || isEditorEl(e.target) || isDragging || isResizing) return;
    if (hovered) hovered.classList.remove('ve-hover');
    hovered = e.target;
    if (!selection.includes(hovered)) hovered.classList.add('ve-hover');
  });
  document.addEventListener('mouseout', () => { if (hovered) hovered.classList.remove('ve-hover'); });

  // ── Double-click to edit text ──
  let isEditing = false;
  document.addEventListener('dblclick', (e) => {
    if (sketchMode || isEditorEl(e.target)) return;
    const target = e.target;
    if (target.tagName === 'IMG' || target.tagName === 'CANVAS') return;
    e.preventDefault();
    e.stopPropagation();
    // Enter edit mode -- disable handles and drag
    isEditing = true;
    clearSelection();
    handlesWrap.innerHTML = '';
    target.contentEditable = true;
    target.style.outline = '2px solid #00ff88';
    target.style.outlineOffset = '2px';
    target.style.cursor = 'text';
    target.focus();
    const range = document.createRange();
    range.selectNodeContents(target);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    const exitEdit = () => {
      isEditing = false;
      target.contentEditable = false;
      target.style.outline = '';
      target.style.outlineOffset = '';
      target.style.cursor = '';
      target.removeEventListener('blur', exitEdit);
      target.removeEventListener('keydown', onKey);
    };
    const onKey = (ev) => {
      if (ev.key === 'Escape') { exitEdit(); ev.stopPropagation(); }
      if (ev.key === 'Enter' && !ev.shiftKey) { exitEdit(); ev.preventDefault(); }
    };
    target.addEventListener('blur', exitEdit);
    target.addEventListener('keydown', onKey);
  }, true);

  // ── Pointer events for select, drag, resize ──
  document.addEventListener('pointerdown', (e) => {
    if (sketchMode || isEditing) return;

    // Handle resize — check BEFORE isEditorEl since handles are inside handlesWrap
    if (e.target.classList.contains('ve-handle')) {
      isResizing = true;
      resizeHandle = e.target.dataset.handle;
      resizeEl = e.target._targetEl;
      const rect = resizeEl.getBoundingClientRect();
      const cs = getComputedStyle(resizeEl);
      resizeStart = {
        x: e.clientX, y: e.clientY,
        w: rect.width, h: rect.height,
        fs: parseFloat(cs.fontSize) || 16,
        // Save all selected elements' start sizes for proportional resize
        all: selection.map(el => {
          const r = el.getBoundingClientRect();
          const c = getComputedStyle(el);
          return { el, w: r.width, h: r.height, fs: parseFloat(c.fontSize) || 16 };
        }),
      };
      // Push undo for all selected elements
      selection.forEach(el => {
        pushUndoBatch([el], el.tagName === 'IMG' ? 'width' : 'font-size');
      });
      e.target.setPointerCapture(e.pointerId);
      e.preventDefault();
      e.stopPropagation();
      return;
    }

    // Skip editor UI elements (toolbar, toggle, etc.)
    if (isEditorEl(e.target)) return;

    // Click to select
    const target = e.target;
    if (e.ctrlKey || e.metaKey) {
      if (selection.includes(target)) {
        selection = selection.filter(el => el !== target);
        target.classList.remove('ve-selected');
      } else {
        addToSelection(target);
      }
      updateHandles();
      updateInfo();
      e.preventDefault();
      return;
    }

    // If clicking on already-selected element or its inline child, start drag
    // Only match children for non-container elements (h1, p, a — not section, div)
    const skipTagsDrag = ['SECTION','BODY','HTML','MAIN','ARTICLE','NAV','HEADER','FOOTER','DIV'];
    const dragMatch = selection.includes(target) ||
      selection.find(el => !skipTagsDrag.includes(el.tagName) && el.contains(target));
    if (dragMatch) {
      isDragging = true;
      dragStart = { x: e.clientX, y: e.clientY };
      dragOffsets = {};
      pushUndoBatch(selection, 'transform');
      selection.forEach(el => {
        const cs = getComputedStyle(el);
        let tx = 0, ty = 0;
        if (cs.transform && cs.transform !== 'none') {
          const m = cs.transform.match(/matrix.*\((.+)\)/);
          if (m) { const v = m[1].split(',').map(Number); tx = v[4] || 0; ty = v[5] || 0; }
        }
        dragOffsets[getSelector(el)] = { tx, ty };
      });
      target.setPointerCapture(e.pointerId);
      e.preventDefault();
      e.stopPropagation();
      return;
    }

    // Smart selection: pick the right element to select
    const skipTags = ['SECTION','BODY','HTML','MAIN','ARTICLE','NAV','HEADER','FOOTER'];
    const inlineTags = ['SPAN','STRONG','EM','B','I','U','SMALL','SUB','SUP','CODE','MARK'];
    const textParentTags = ['H1','H2','H3','H4','H5','H6','P','A','LI','LABEL','BUTTON','FIGCAPTION'];

    let selTarget = target;

    // If clicking an inline element, walk up to its text parent (h1, p, a, etc.)
    // so "DUBERY" + "MNL" spans are treated as one h1 element
    if (inlineTags.includes(selTarget.tagName)) {
      let parent = selTarget.parentElement;
      while (parent && !textParentTags.includes(parent.tagName) && !skipTags.includes(parent.tagName)) {
        parent = parent.parentElement;
      }
      if (parent && textParentTags.includes(parent.tagName)) {
        selTarget = parent;
      }
    }

    // Never select layout containers
    if (skipTags.includes(selTarget.tagName)) return;
    if (selTarget.tagName === 'DIV' && selTarget.children.length > 1) return;
    if (selTarget === document.body) return;

    clearSelection();
    addToSelection(selTarget);
    e.preventDefault();
  }, true);

  document.addEventListener('pointermove', (e) => {
    if (isDragging) {
      const dx = e.clientX - dragStart.x;
      const dy = e.clientY - dragStart.y;
      selection.forEach(el => {
        const sel = getSelector(el);
        const off = dragOffsets[sel] || { tx: 0, ty: 0 };
        const v = `translate(${off.tx + dx}px, ${off.ty + dy}px)`;
        forceStyle(el, 'transform', v);
        recordChange(el, 'transform', v);
      });
      updateHandles();
    }

    if (isResizing && resizeEl) {
      const dx = e.clientX - resizeStart.x;
      const dy = e.clientY - resizeStart.y;
      const h = resizeHandle;

      // Determine axis mode
      // Edge handles: single axis. Corners: free (both axes), Shift = proportional
      const isEdge = ['t','b','l','r'].includes(h);
      const isCorner = ['tl','tr','bl','br'].includes(h);

      let ratioW = 1, ratioH = 1;

      if (h === 'r')  ratioW = (resizeStart.w + dx) / resizeStart.w;
      if (h === 'l')  ratioW = (resizeStart.w - dx) / resizeStart.w;
      if (h === 'b')  ratioH = (resizeStart.h + dy) / resizeStart.h;
      if (h === 't')  ratioH = (resizeStart.h - dy) / resizeStart.h;

      if (isCorner) {
        const sdx = (h === 'tl' || h === 'bl') ? -dx : dx;
        const sdy = (h === 'tl' || h === 'tr') ? -dy : dy;
        if (e.shiftKey) {
          // Shift held = proportional (linked X and Y)
          const scale = Math.max(sdx, sdy);
          ratioW = (resizeStart.w + scale) / resizeStart.w;
          ratioH = ratioW;
        } else {
          // Free resize
          ratioW = (resizeStart.w + sdx) / resizeStart.w;
          ratioH = (resizeStart.h + sdy) / resizeStart.h;
        }
      }

      ratioW = Math.max(0.1, ratioW);
      ratioH = Math.max(0.1, ratioH);

      // Apply to ALL selected elements
      (resizeStart.all || []).forEach(({ el, w, h: elH, fs }) => {
        if (el.tagName === 'IMG') {
          const newW = Math.max(20, Math.round(w * ratioW));
          forceStyle(el, 'width', newW + 'px');
          forceStyle(el, 'max-width', 'none');
          if (isEdge && (resizeHandle === 't' || resizeHandle === 'b')) {
            const newH = Math.max(20, Math.round(elH * ratioH));
            forceStyle(el, 'height', newH + 'px');
          } else if (isCorner && !e.shiftKey) {
            const newH = Math.max(20, Math.round(elH * ratioH));
            forceStyle(el, 'height', newH + 'px');
          } else {
            forceStyle(el, 'height', 'auto');
          }
          recordChange(el, 'width', newW + 'px');
        } else {
          // Text: resize changes WIDTH (causes text wrap), not font-size
          const newW = Math.max(40, Math.round(w * ratioW));
          forceStyle(el, 'width', newW + 'px');
          forceStyle(el, 'max-width', 'none');
          forceStyle(el, 'overflow-wrap', 'break-word');
          recordChange(el, 'width', newW + 'px');
        }
      });

      // Show size label
      const pw = Math.max(20, Math.round(resizeStart.w * ratioW));
      const ph = Math.max(20, Math.round(resizeStart.h * ratioH));
      sizeLabel.textContent = `${pw} × ${ph}`;
      // Position size label near cursor
      sizeLabel.style.display = 'block';
      sizeLabel.style.left = (e.clientX + 12) + 'px';
      sizeLabel.style.top = (e.clientY - 8) + 'px';
      updateHandles();
    }
  });

  document.addEventListener('pointerup', () => {
    if (isDragging) {
      isDragging = false;
      // Save final positions
      selection.forEach(el => {
        const cs = getComputedStyle(el);
        if (cs.transform && cs.transform !== 'none') {
          recordChange(el, 'transform', cs.transform);
        }
      });
    }
    if (isResizing) {
      isResizing = false;
      resizeEl = null;
      sizeLabel.style.display = 'none';
    }
  });

  // ── Color controls ──
  $('ve-color').addEventListener('input', (e) => {
    if (selection.length === 0) return;
    pushUndoBatch(selection, 'color');
    selection.forEach(el => { forceStyle(el, 'color', e.target.value); recordChange(el, 'color', e.target.value); });
  });
  $('ve-bg').addEventListener('input', (e) => {
    if (selection.length === 0) return;
    pushUndoBatch(selection, 'background-color');
    selection.forEach(el => { forceStyle(el, 'background-color', e.target.value); recordChange(el, 'background-color', e.target.value); });
  });

  // ── Add Elements ──
  let addedCount = 0;

  // Find the best insertion point and method
  const getInsertInfo = () => {
    // If something is selected, insert after it within its parent
    if (selection.length > 0) {
      const el = selection[selection.length - 1];
      return { parent: el.parentElement, after: el };
    }
    // Otherwise find the section-inner or section most visible in viewport
    const containers = document.querySelectorAll('.section-inner, .flow-section, .hero-standalone');
    const vpMid = window.innerHeight / 2;
    let best = null, bestDist = Infinity;
    containers.forEach(s => {
      const rect = s.getBoundingClientRect();
      const mid = rect.top + rect.height / 2;
      const dist = Math.abs(mid - vpMid);
      if (dist < bestDist) { bestDist = dist; best = s; }
    });
    return { parent: best || document.body, after: null };
  };

  $('ve-add-text').addEventListener('click', () => {
    addedCount++;
    const el = document.createElement('p');
    el.className = 've-added ve-added-' + addedCount;
    el.textContent = 'New text';
    el.style.cssText = `
      font-family: var(--font-display); font-size: 24px; font-weight: 600;
      color: #fff; padding: 4px 8px; min-width: 40px; margin-top: 1rem;
      position: relative; z-index: 10;
    `;
    const info = getInsertInfo();
    if (info.after) info.after.insertAdjacentElement('afterend', el);
    else info.parent.appendChild(el);
    clearSelection();
    addToSelection(el);
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Enter edit mode immediately
    isEditing = true;
    handlesWrap.innerHTML = '';
    el.contentEditable = true;
    el.style.outline = '2px solid #00ff88';
    el.style.outlineOffset = '2px';
    el.style.cursor = 'text';
    el.focus();
    document.execCommand('selectAll');
    const exitEdit = () => {
      isEditing = false;
      el.contentEditable = false;
      el.style.outline = '';
      el.style.outlineOffset = '';
      el.style.cursor = '';
    };
    const onKey = (ev) => {
      if (ev.key === 'Escape') { exitEdit(); ev.stopPropagation(); el.removeEventListener('keydown', onKey); }
      if (ev.key === 'Enter' && !ev.shiftKey) { exitEdit(); ev.preventDefault(); el.removeEventListener('keydown', onKey); }
    };
    el.addEventListener('blur', exitEdit, { once: true });
    el.addEventListener('keydown', onKey);
  });

  $('ve-add-img').addEventListener('click', () => {
    $('ve-file-input').click();
  });

  $('ve-file-input').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    addedCount++;
    const reader = new FileReader();
    const fileName = file.name;
    // Try to get full path (webkitRelativePath or name)
    const filePath = file.webkitRelativePath || file.name;
    reader.onload = (ev) => {
      const el = document.createElement('img');
      el.className = 've-added ve-added-' + addedCount;
      el.src = ev.target.result;
      el._filePath = filePath;
      el._fileName = fileName;
      el.style.cssText = `
        width: 200px; height: auto; border-radius: 4px; margin-top: 1rem;
        display: block; position: relative; z-index: 10;
      `;
      const info = getInsertInfo();
      if (info.after) info.after.insertAdjacentElement('afterend', el);
      else info.parent.appendChild(el);
      clearSelection();
      addToSelection(el);
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  });

  // ── Sketch ──
  $('ve-sketch-toggle').addEventListener('click', () => {
    sketchMode = !sketchMode;
    $('ve-sketch-toggle').textContent = sketchMode ? 'Pen ON' : 'Pen';
    $('ve-sketch-toggle').classList.toggle('ve-active', sketchMode);
    sketchCanvas.style.display = sketchMode ? 'block' : 'none';
    if (sketchMode) clearSelection();
  });
  $('ve-sk-color').addEventListener('input', (e) => { sketchColor = e.target.value; });

  sketchCanvas.addEventListener('pointerdown', (e) => {
    isDrawing = true;
    const snapshot = skCtx.getImageData(0, 0, sketchCanvas.width, sketchCanvas.height);
    undoStack.push({ type: 'sketch', snapshot });
    updateUndoUI();
    skCtx.beginPath();
    skCtx.moveTo(e.clientX, e.clientY);
    skCtx.strokeStyle = sketchColor;
    skCtx.lineWidth = sketchWidth;
    skCtx.lineCap = 'round';
    skCtx.lineJoin = 'round';
  });
  sketchCanvas.addEventListener('pointermove', (e) => { if (!isDrawing) return; skCtx.lineTo(e.clientX, e.clientY); skCtx.stroke(); });
  sketchCanvas.addEventListener('pointerup', () => { isDrawing = false; });
  sketchCanvas.addEventListener('pointerleave', () => { isDrawing = false; });

  // ── Export ──
  $('ve-export').addEventListener('click', () => {
    // Collect ALL added elements with full state
    const addedEls = document.querySelectorAll('.ve-added');
    let elementsInfo = '';
    addedEls.forEach((el, i) => {
      const cs = getComputedStyle(el);
      const isHidden = cs.display === 'none' || el.style.display === 'none';
      const parent = el.parentElement ? getSelector(el.parentElement) : 'body';
      const prev = el.previousElementSibling ? getSelector(el.previousElementSibling) : '(first child)';

      // Get transform as x,y
      let tx = 0, ty = 0;
      if (cs.transform && cs.transform !== 'none') {
        const m = cs.transform.match(/matrix.*\((.+)\)/);
        if (m) { const v = m[1].split(',').map(Number); tx = Math.round(v[4] || 0); ty = Math.round(v[5] || 0); }
      }

      if (el.tagName === 'IMG') {
        const path = el._filePath || el._fileName || '(unknown)';
        elementsInfo += `/* IMAGE ${i + 1}: ${path}\n`;
        elementsInfo += `   Status: ${isHidden ? 'DELETED' : 'VISIBLE'}\n`;
        elementsInfo += `   Inside: ${parent} | After: ${prev}\n`;
        elementsInfo += `   Position: x=${tx}, y=${ty}\n`;
        elementsInfo += `   Size: ${cs.width} x ${cs.height} */\n\n`;
      }
      if (el.tagName === 'P') {
        elementsInfo += `/* TEXT ${i + 1}: "${el.textContent.substring(0, 60)}"\n`;
        elementsInfo += `   Status: ${isHidden ? 'DELETED' : 'VISIBLE'}\n`;
        elementsInfo += `   Inside: ${parent} | After: ${prev}\n`;
        elementsInfo += `   Position: x=${tx}, y=${ty}\n`;
        elementsInfo += `   Font: ${cs.fontSize} | Color: ${cs.color} */\n\n`;
      }
    });

    // Collect CSS changes, but skip generic 'img' selector (replaced by per-element tracking above)
    let css = elementsInfo;
    for (const [sel, props] of Object.entries(changes)) {
      if (sel === 'img') continue; // skip generic img, tracked per-element above
      css += `${sel} {\n`;
      for (const [prop, val] of Object.entries(props)) css += `  ${prop}: ${val};\n`;
      css += '}\n\n';
    }

    if (!css.trim()) {
      exportToast.textContent = '/* No changes yet */';
      exportToast.style.display = 'block';
      setTimeout(() => { exportToast.style.display = 'none'; }, 2000);
      return;
    }

    exportToast.textContent = css;
    exportToast.style.display = 'block';
    navigator.clipboard.writeText(css).then(() => {
      $('ve-info').textContent = 'Copied to clipboard!';
      setTimeout(() => updateInfo(), 2000);
    }).catch(() => {});
    setTimeout(() => { exportToast.style.display = 'none'; }, 8000);
  });

  // ── Keyboard ──
  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'Escape') {
      clearSelection();
      if (sketchMode) { sketchMode = false; $('ve-sketch-toggle').textContent = 'Pen'; $('ve-sketch-toggle').classList.remove('ve-active'); sketchCanvas.style.display = 'none'; }
      exportToast.style.display = 'none';
    }
    if (e.key === 'e' && !isEditing) toggleToolbar();
    if (e.key === 'Enter' && !isEditing && selection.length > 0) {
      e.preventDefault();
      clearSelection();
      $('ve-info').textContent = 'Embedded. Click to select another.';
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'z') { e.preventDefault(); doUndo(); }
    if (e.key === 'Delete' || e.key === 'Backspace') {
      if (selection.length > 0) {
        pushUndoBatch(selection, 'display');
        selection.forEach(el => { forceStyle(el, 'display', 'none'); recordChange(el, 'display', 'none'); });
        clearSelection();
      }
    }
    // Arrow nudge
    if (selection.length > 0 && ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key)) {
      e.preventDefault();
      const step = e.shiftKey ? 20 : 5;
      const map = { ArrowUp: [0,-step], ArrowDown: [0,step], ArrowLeft: [-step,0], ArrowRight: [step,0] };
      const [dx, dy] = map[e.key];
      pushUndoBatch(selection, 'transform');
      selection.forEach(el => {
        const cs = getComputedStyle(el);
        let tx = 0, ty = 0;
        if (cs.transform && cs.transform !== 'none') {
          const m = cs.transform.match(/matrix.*\((.+)\)/);
          if (m) { const v = m[1].split(',').map(Number); tx = v[4] || 0; ty = v[5] || 0; }
        }
        const nv = `translate(${tx + dx}px, ${ty + dy}px)`;
        forceStyle(el, 'transform', nv);
        recordChange(el, 'transform', nv);
      });
      updateHandles();
    }
  });

  // Sync color pickers when selection changes
  const origAdd = addToSelection;

  console.log('%c[DuberyMNL Editor v3] Direct manipulation mode — drag to move, corners to resize', 'color: #E8110F; font-weight: bold');
})();
