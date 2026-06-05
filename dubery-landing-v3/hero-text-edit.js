/* hero-text-edit.js — visual overlay editor for the hero copy (mobile-first).
   Activates on ?edittext (kept separate from ?edit's image-framing editor).
   Lets you: click-to-edit text, drag the copy block + buttons, resize/restyle
   fonts, delete elements, then export the edits as JSON to bake into the site. */
(function () {
  var s = location.search;
  if (s.indexOf('edittext') === -1) return;

  document.addEventListener('DOMContentLoaded', init);

  var slides, activeIdx = 0, selected = null;
  var origHTML = new Map();

  // setPointerCapture throws "No active pointer" if the OS cancels the touch
  // between pointerdown and this call (real-device multi-touch / cancel races).
  // Capture is a nice-to-have for drags, so never let it abort one.
  function capture(el, id) { try { el.setPointerCapture(id); } catch (e) {} }

  function roleMap(slide) {
    var copy = slide.querySelector('.hero-primary-copy');
    var btns = slide.querySelectorAll('.cta-row .btn');
    return {
      eyebrow: copy && copy.querySelector('.eyebrow'),
      h1:      copy && copy.querySelector('h1'),
      lede:    copy && copy.querySelector('.lede'),
      meta:    copy && copy.querySelector('.hero-meta'),
      btn1:    btns[0],
      btn2:    btns[1]
    };
  }

  function init() {
    slides = Array.prototype.slice.call(document.querySelectorAll('.hero-slide'));
    if (!slides.length) return;
    injectStyles();
    var panel = buildPanel();
    document.body.appendChild(panel);
    makePanelMovable(panel);
    slides.forEach(prepSlide);
    wireToolbar();
    gotoSlide(0);
  }

  /* ---- prepare a slide for editing ---- */
  function prepSlide(slide) {
    // stop hero links from navigating while editing
    slide.addEventListener('click', function (e) {
      var a = e.target.closest('a');
      if (a) { e.preventDefault(); }
    }, true);

    var copy = slide.querySelector('.hero-primary-copy');
    var cta = slide.querySelector('.cta-row');
    if (!copy) return;

    // make text elements editable + selectable
    var roles = roleMap(slide);
    Object.keys(roles).forEach(function (role) {
      var el = roles[role];
      if (!el) return;
      origHTML.set(el, el.innerHTML);
      el.setAttribute('contenteditable', 'true');
      el.dataset.hetRole = role;
      el.addEventListener('focus', function () { setSelected(el); });
      el.addEventListener('pointerdown', function () { setSelected(el); });
    });

    // drag grips:
    //   red   ✛ (top-left)  = move the whole copy block at once
    //   blue  ✛ (top-right) = move that ONE text box on its own
    //   green ✛ (top-right) = move the button row
    addGrip(copy, slide, true, 'move whole block');
    attachTextGrips(slide);
    if (cta) addGrip(cta, copy, false, 'move buttons');
  }

  // a small blue ✛ on each individual text box so it can be dragged on its own.
  // Re-runnable: resetSlide restores innerHTML (which strips these inner grips),
  // so it calls this again to put them back.
  function attachTextGrips(slide) {
    var copy = slide.querySelector('.hero-primary-copy');
    if (!copy) return;
    var roles = roleMap(slide);
    ['eyebrow', 'h1', 'lede', 'meta'].forEach(function (role) {
      var el = roles[role];
      if (el && !el.querySelector(':scope > .het-grip-el')) {
        addGrip(el, copy, false, 'move this text', 'het-grip-el');
      }
    });
  }

  function addGrip(target, container, isBlock, label, variant) {
    var grip = document.createElement('button');
    grip.type = 'button';
    grip.className = 'het-grip ' + (variant || (isBlock ? 'het-grip-block' : 'het-grip-cta'));
    grip.title = label;
    grip.textContent = '✛';
    grip.contentEditable = 'false';   // grips live inside contenteditable text boxes — keep them non-editable
    // anchor the grip relative to its target
    if (getComputedStyle(target).position === 'static') target.style.position = 'relative';
    target.appendChild(grip);

    var dragging = false, grabX = 0, grabY = 0;
    grip.addEventListener('pointerdown', function (e) {
      e.preventDefault(); e.stopPropagation();
      ensureAbsolute(target, container, isBlock);
      var tr = target.getBoundingClientRect();
      grabX = e.clientX - tr.left; grabY = e.clientY - tr.top;
      dragging = true; capture(grip, e.pointerId);
    });
    grip.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      var cr = container.getBoundingClientRect();
      var leftPct = (e.clientX - grabX - cr.left) / cr.width * 100;
      var topPct  = (e.clientY - grabY - cr.top) / cr.height * 100;
      leftPct = Math.max(-5, Math.min(95, leftPct));
      topPct  = Math.max(-8, Math.min(96, topPct));
      target.style.left = leftPct.toFixed(1) + '%';
      target.style.top  = topPct.toFixed(1) + '%';
      e.preventDefault();
    });
    function end() { dragging = false; }
    grip.addEventListener('pointerup', end);
    grip.addEventListener('pointercancel', end);
  }

  // convert an element to absolute positioning (once) without it jumping
  function ensureAbsolute(target, container, isBlock) {
    if (target.dataset.hetAbs) return;
    var r = target.getBoundingClientRect();
    var cr = container.getBoundingClientRect();
    target.style.position = 'absolute';
    if (isBlock) { target.style.height = 'auto'; target.style.margin = '0'; target.style.maxWidth = '72%'; }
    else { target.style.width = r.width + 'px'; target.style.margin = '0'; }   // pin width so a text box doesn't reflow when it leaves the flow
    target.style.left = ((r.left - cr.left) / cr.width * 100).toFixed(1) + '%';
    target.style.top  = ((r.top - cr.top) / cr.height * 100).toFixed(1) + '%';
    target.dataset.hetAbs = '1';
  }

  /* ---- selection ---- */
  function setSelected(el) {
    if (selected) selected.classList.remove('het-selected');
    selected = el;
    el.classList.add('het-selected');
    var name = el.dataset.hetRole || el.tagName.toLowerCase();
    document.getElementById('het-selname').textContent = name;
    showStretch(el);
  }

  /* ---- toolbar ---- */
  function buildPanel() {
    var opts = slides.map(function (_, i) {
      return '<option value="' + i + '">Slide ' + (i + 1) + '</option>';
    }).join('');
    var p = document.createElement('div');
    p.id = 'het';
    p.innerHTML =
      '<div class="het-head" id="het-head">Overlay Editor<span id="het-min" title="Collapse">–</span></div>' +
      '<div id="het-body">' +
      '<div class="het-hint">Tap text to type. Drag ✛ grips — <b style="color:#ff8a7a">red</b>: whole block · <b style="color:#7ab8ff">blue</b>: that text box · <b style="color:#7fd99a">green</b>: buttons. Select an element for size / font / delete.</div>' +
      '<label>Slide <select id="het-slide">' + opts + '</select></label>' +
      '<div class="het-sel">Selected: <b id="het-selname">—</b></div>' +
      '<div class="het-row"><button id="het-fdn">A−</button><button id="het-fup">A+</button>' +
      '<select id="het-fam"><option value="">Font…</option>' +
      '<option value="\'Anton\', sans-serif">Anton</option>' +
      '<option value="\'Archivo\', sans-serif">Archivo</option>' +
      '<option value="\'Caveat\', cursive">Caveat</option>' +
      '<option value="\'Space Grotesk\', sans-serif">Grotesk</option>' +
      '<option value="\'Inter\', sans-serif">Inter</option></select></div>' +
      '<div class="het-row"><span class="het-cap">Wide<b id="het-sx">100%</b></span>' +
      '<button id="het-stdn" title="Narrower">↔ −</button><button id="het-stup" title="Wider">↔ +</button></div>' +
      '<div class="het-row"><span class="het-cap">Tall<b id="het-sy">100%</b></span>' +
      '<button id="het-styn" title="Shorter">↕ −</button><button id="het-styp" title="Taller">↕ +</button></div>' +
      '<div class="het-row"><button id="het-del">🗑 Delete</button><button id="het-reset">↺ Reset slide</button></div>' +
      '<button id="het-copy">Copy Slide</button>' +
      '<button id="het-copyall">Copy All</button>' +
      '<div id="het-out"></div>' +
      '</div><div id="het-resize" title="Drag to resize"></div>';
    return p;
  }

  function wireToolbar() {
    document.getElementById('het-slide').addEventListener('change', function () {
      gotoSlide(+this.value);
    });
    document.getElementById('het-fup').addEventListener('click', function () { bumpFont(1); });
    document.getElementById('het-fdn').addEventListener('click', function () { bumpFont(-1); });
    document.getElementById('het-stup').addEventListener('click', function () { bumpStretch('x', 0.1); });
    document.getElementById('het-stdn').addEventListener('click', function () { bumpStretch('x', -0.1); });
    document.getElementById('het-styp').addEventListener('click', function () { bumpStretch('y', 0.1); });
    document.getElementById('het-styn').addEventListener('click', function () { bumpStretch('y', -0.1); });
    document.getElementById('het-fam').addEventListener('change', function () {
      if (selected && this.value) selected.style.fontFamily = this.value;
    });
    document.getElementById('het-del').addEventListener('click', function () {
      if (!selected) return;
      selected.classList.add('het-hidden');
      selected.style.display = 'none';
    });
    document.getElementById('het-reset').addEventListener('click', resetSlide);
    document.getElementById('het-copy').addEventListener('click', function () {
      copyText(JSON.stringify(exportSlide(activeIdx), null, 2), this, 'Copy Slide');
    });
    document.getElementById('het-copyall').addEventListener('click', function () {
      var all = slides.map(function (_, i) { return exportSlide(i); }).filter(hasEdits);
      copyText(JSON.stringify(all, null, 2), this, 'Copy All');
    });
  }

  function bumpFont(dir) {
    if (!selected) return;
    var px = parseFloat(getComputedStyle(selected).fontSize) || 16;
    selected.style.fontSize = Math.max(8, px + dir) + 'px';
  }

  // stretch — scaleX (Wide) / scaleY (Tall), anchored top-left so the box's
  // positioned corner stays put while the letters get wider / taller.
  function bumpStretch(axis, dir) {
    if (!selected) return;
    var key = axis === 'y' ? 'hetSy' : 'hetSx';
    var cur = parseFloat(selected.dataset[key] || '1');
    selected.dataset[key] = Math.max(0.5, Math.min(2.5, +(cur + dir).toFixed(2)));
    applyStretch(selected);
    showStretch(selected);
  }
  function applyStretch(el) {
    var sx = parseFloat(el.dataset.hetSx || '1'), sy = parseFloat(el.dataset.hetSy || '1');
    el.style.transformOrigin = 'left top';
    el.style.transform = 'scaleX(' + sx + ') scaleY(' + sy + ')';
  }
  function showStretch(el) {
    var x = document.getElementById('het-sx'), y = document.getElementById('het-sy');
    if (x) x.textContent = Math.round(parseFloat(el.dataset.hetSx || '1') * 100) + '%';
    if (y) y.textContent = Math.round(parseFloat(el.dataset.hetSy || '1') * 100) + '%';
  }

  function gotoSlide(i) {
    activeIdx = i;
    document.getElementById('het-slide').value = String(i);
    if (window._heroGoTo) window._heroGoTo(i);
  }

  function resetSlide() {
    var slide = slides[activeIdx];
    var roles = roleMap(slide);
    Object.keys(roles).forEach(function (role) {
      var el = roles[role];
      if (!el) return;
      el.classList.remove('het-hidden', 'het-selected');
      el.style.display = ''; el.style.fontSize = ''; el.style.fontFamily = '';
      el.style.position = ''; el.style.left = ''; el.style.top = '';
      el.style.width = ''; el.style.margin = '';
      el.style.transform = ''; el.style.transformOrigin = '';
      delete el.dataset.hetAbs; delete el.dataset.hetSx; delete el.dataset.hetSy;
      if (origHTML.has(el)) el.innerHTML = origHTML.get(el);
    });
    var copy = slide.querySelector('.hero-primary-copy');
    var cta = slide.querySelector('.cta-row');
    [copy, cta].forEach(function (t) {
      if (!t) return;
      t.style.position = ''; t.style.left = ''; t.style.top = '';
      t.style.height = ''; t.style.margin = ''; t.style.maxWidth = '';
      delete t.dataset.hetAbs;
    });
    attachTextGrips(slide);   // innerHTML reset stripped the inner per-text grips — put them back
    selected = null;
    document.getElementById('het-selname').textContent = '—';
  }

  /* ---- export ---- */
  function exportSlide(i) {
    var slide = slides[i];
    var copy = slide.querySelector('.hero-primary-copy');
    var cta = slide.querySelector('.cta-row');
    var out = { slide: i + 1 };
    if (copy && (copy.style.left || copy.style.top)) out.block = { left: copy.style.left, top: copy.style.top };
    if (cta && (cta.style.left || cta.style.top)) out.buttons = { left: cta.style.left, top: cta.style.top };
    var roles = roleMap(slide);
    var fonts = {}, text = {}, hidden = [], positions = {}, stretch = {};
    Object.keys(roles).forEach(function (role) {
      var el = roles[role];
      if (!el) return;
      if (el.classList.contains('het-hidden')) { hidden.push(role); return; }
      if (el.style.left || el.style.top) positions[role] = { left: el.style.left, top: el.style.top };
      var st = {};
      if (el.dataset.hetSx && parseFloat(el.dataset.hetSx) !== 1) st.x = parseFloat(el.dataset.hetSx);
      if (el.dataset.hetSy && parseFloat(el.dataset.hetSy) !== 1) st.y = parseFloat(el.dataset.hetSy);
      if (st.x || st.y) stretch[role] = st;
      var f = {};
      if (el.style.fontSize) f.size = el.style.fontSize;
      if (el.style.fontFamily) f.family = el.style.fontFamily;
      if (f.size || f.family) fonts[role] = f;
      var html = cleanHTML(el);
      if (origHTML.has(el) && html !== origHTML.get(el).trim()) text[role] = html;
    });
    if (Object.keys(positions).length) out.positions = positions;
    if (Object.keys(stretch).length) out.stretch = stretch;
    if (Object.keys(fonts).length) out.fonts = fonts;
    if (Object.keys(text).length) out.text = text;
    if (hidden.length) out.hidden = hidden;
    return out;
  }

  function cleanHTML(el) {
    var c = el.cloneNode(true);
    c.querySelectorAll('.het-grip').forEach(function (g) { g.remove(); });
    return c.innerHTML.trim();
  }

  function hasEdits(o) {
    return o.block || o.buttons || o.positions || o.stretch || o.fonts || o.text || o.hidden;
  }

  function copyText(text, btn, label) {
    document.getElementById('het-out').textContent = text;
    function done() { btn.textContent = 'Copied!'; setTimeout(function () { btn.textContent = label; }, 1400); }
    if (navigator.clipboard) { navigator.clipboard.writeText(text).then(done, done); }
    else {
      var ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); } catch (e) {}
      document.body.removeChild(ta); done();
    }
  }

  /* ---- movable / resizable / collapsible panel ---- */
  function makePanelMovable(panel) {
    var head = document.getElementById('het-head');
    var minBtn = document.getElementById('het-min');
    var rz = document.getElementById('het-resize');
    function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
    // Detach the panel from its CSS anchor (top-right on desktop, bottom-dock on
    // mobile) to absolute left/top — done lazily on first drag/resize so the
    // resting position stays whatever CSS dictates until the user moves it.
    function pinXY() {
      if (panel.dataset.hetPinned) return;
      var r = panel.getBoundingClientRect();
      panel.style.left = r.left + 'px'; panel.style.top = r.top + 'px';
      panel.style.right = 'auto'; panel.style.bottom = 'auto';
      panel.style.width = r.width + 'px';
      panel.dataset.hetPinned = '1';
    }
    var moving = false, mx = 0, my = 0, ox = 0, oy = 0;
    head.addEventListener('pointerdown', function (e) {
      if (e.target === minBtn) return;
      pinXY();
      moving = true; mx = e.clientX; my = e.clientY;
      var r = panel.getBoundingClientRect(); ox = r.left; oy = r.top;
      capture(head, e.pointerId); e.preventDefault();
    });
    head.addEventListener('pointermove', function (e) {
      if (!moving) return;
      panel.style.left = clamp(ox + (e.clientX - mx), 0, window.innerWidth - 40) + 'px';
      panel.style.top  = clamp(oy + (e.clientY - my), 0, window.innerHeight - 36) + 'px';
      e.preventDefault();
    });
    head.addEventListener('pointerup', function () { moving = false; });
    head.addEventListener('pointercancel', function () { moving = false; });
    minBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var c = panel.classList.toggle('het-collapsed');
      minBtn.textContent = c ? '+' : '–';
    });
    var sizing = false, sx = 0, sy = 0, sw = 0, sh = 0;
    rz.addEventListener('pointerdown', function (e) {
      pinXY();
      sizing = true; sx = e.clientX; sy = e.clientY;
      var r = panel.getBoundingClientRect(); sw = r.width; sh = r.height;
      capture(rz, e.pointerId); e.preventDefault();
    });
    rz.addEventListener('pointermove', function (e) {
      if (!sizing) return;
      panel.style.width  = clamp(sw + (e.clientX - sx), 170, window.innerWidth * 0.95) + 'px';
      panel.style.height = clamp(sh + (e.clientY - sy), 130, window.innerHeight * 0.9) + 'px';
      panel.style.maxHeight = 'none'; e.preventDefault();
    });
    rz.addEventListener('pointerup', function () { sizing = false; });
    rz.addEventListener('pointercancel', function () { sizing = false; });
  }

  /* ---- styles ---- */
  function injectStyles() {
    var css = [
      '#het{position:fixed;top:80px;right:12px;z-index:99999;background:rgba(0,0,0,.9);color:#fff;',
      'padding:12px;border-radius:12px;font:13px/1.45 system-ui;width:230px;box-sizing:border-box;',
      'display:flex;flex-direction:column;max-height:88vh;box-shadow:0 4px 22px rgba(0,0,0,.55);}',
      '#het .het-head{font-weight:700;font-size:14px;margin-bottom:8px;cursor:move;user-select:none;',
      'touch-action:none;display:flex;justify-content:space-between;align-items:center;}',
      '#het #het-min{cursor:pointer;padding:0 2px 0 10px;opacity:.85;font-size:16px;}',
      '#het #het-body{flex:1 1 auto;min-height:0;overflow-y:auto;}',
      '#het.het-collapsed #het-body,#het.het-collapsed #het-resize{display:none;}',
      '#het.het-collapsed{max-height:none;}',
      '#het .het-hint{font-size:11px;opacity:.72;margin-bottom:10px;}',
      '#het label{display:block;margin-bottom:8px;}',
      '#het select{width:100%;margin-top:3px;background:#222;color:#fff;border:1px solid #555;border-radius:5px;padding:3px 6px;}',
      '#het .het-sel{font-size:12px;margin-bottom:8px;opacity:.9;}',
      '#het .het-sel b{color:#ffd27a;}',
      '#het .het-row{display:flex;gap:6px;margin-bottom:8px;}',
      '#het .het-row>*{flex:1;}',
      '#het .het-cap{display:flex;flex-direction:column;align-items:flex-start;justify-content:center;',
      'font-size:10px;line-height:1.1;opacity:.8;}',
      '#het .het-cap b{color:#ffd27a;font-size:12px;}',
      '#het button{background:#1f2937;color:#fff;border:1px solid #374151;border-radius:6px;',
      'padding:6px;cursor:pointer;font-weight:600;font-size:12px;}',
      '#het #het-fup,#het #het-fdn{font-size:14px;}',
      '#het #het-copy{width:100%;background:#D7392A;border-color:#D7392A;margin-top:2px;}',
      '#het #het-copyall{width:100%;margin-top:6px;}',
      '#het #het-out{font-size:10px;background:rgba(255,255,255,.1);padding:6px;border-radius:6px;',
      'margin-top:8px;max-height:120px;overflow:auto;white-space:pre-wrap;word-break:break-all;}',
      '#het #het-resize{position:absolute;right:3px;bottom:3px;width:18px;height:18px;cursor:nwse-resize;',
      'touch-action:none;border-radius:0 0 8px 0;background:repeating-linear-gradient(135deg,rgba(255,255,255,.5) 0 2px,transparent 2px 4px);}',
      // in-page editing affordances
      '.het-selected{outline:2px dashed #ffd27a !important;outline-offset:2px;}',
      '[contenteditable=true]:focus{outline:2px solid #4ea1ff !important;outline-offset:2px;}',
      // lock the hero photo while editing: kill native image selection / drag and
      // let taps fall through to the text + grips (the copy block sits above it).
      '.hero-primary-media,.hero-primary-media img{user-select:none;-webkit-user-select:none;-webkit-user-drag:none;}',
      '.hero-primary-media img{pointer-events:none;}',
      '.het-grip{position:absolute;top:-5px;left:-5px;width:9px;height:9px;border-radius:50%;padding:0;',
      'border:none;background:#D7392A;color:#fff;font-size:7px;line-height:1;cursor:move;z-index:50;',
      'touch-action:none;box-shadow:0 1px 3px rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;}',
      // invisible larger grab area so the tiny dot is still easy to drag (does not block the view)
      '.het-grip::before{content:"";position:absolute;inset:-8px;}',
      '.het-grip-cta{background:#2b7a3b;top:-5px;left:auto;right:-5px;}',
      '.het-grip-el{background:#2f6dd0;top:-5px;left:auto;right:-5px;}',
      // mobile (<=720px): dock the panel as a full-width bottom bar so it can never
      // sit off-screen, with finger-sized tap targets + grips. Scoped to the media
      // query; only loads under ?edittext so it never ships to production users.
      '@media (max-width:720px){',
      '#het{top:auto;bottom:0;left:0;right:0;width:auto;max-height:34vh;border-radius:12px 12px 0 0;',
      'padding:8px 12px calc(8px + env(safe-area-inset-bottom));font-size:12px;}',
      '#het .het-head{font-size:14px;padding:1px 0 5px;}',
      '#het #het-min{font-size:22px;padding:2px 6px 2px 14px;}',
      '#het .het-hint{font-size:10.5px;line-height:1.35;margin-bottom:7px;}',
      '#het label,#het .het-sel,#het .het-row{margin-bottom:6px;}',
      '#het select{min-height:38px;font-size:14px;padding:6px;}',
      '#het button{min-height:40px;font-size:13px;padding:8px;touch-action:manipulation;}',
      '#het #het-fup,#het #het-fdn{font-size:17px;}',
      '#het #het-out{max-height:64px;}',
      '#het #het-resize{display:none;}',
      '#het.het-collapsed{bottom:0;}',
      '.het-grip{width:10px;height:10px;top:-6px;left:-6px;font-size:8px;}',
      '.het-grip-cta{top:-6px;left:auto;right:-6px;}',
      '.het-grip-el{top:-6px;left:auto;right:-6px;}',
      '}'
    ].join('');
    var st = document.createElement('style');
    st.textContent = css;
    document.head.appendChild(st);
  }
})();
