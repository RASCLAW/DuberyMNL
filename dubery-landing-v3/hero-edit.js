(function () {
  if (!location.search.includes('edit')) return;

  document.addEventListener('DOMContentLoaded', function () {
    var imgs = document.querySelectorAll('.hero-primary-media img');
    if (!imgs.length) return;
    var img = imgs[0];
    var activeIdx = 0;
    var slideState = {}; // remembers {x,y,z} per slide index across slide switches

    function getPosFrom(el) {
      var computed = getComputedStyle(el);
      var pos = (computed.objectPosition || '49% 44%').split(' ');
      return { x: parseFloat(pos[0]) || 49, y: parseFloat(pos[1]) || 44 };
    }

    // With object-fit:contain, this is the scale that makes the image fill the
    // frame (i.e. cover-equivalent). Used as the default starting zoom.
    function fillZoom(el) {
      var bw = el.clientWidth, bh = el.clientHeight, iw = el.naturalWidth, ih = el.naturalHeight;
      if (!bw || !bh || !iw || !ih) return 1;
      return Math.max(bw / iw, bh / ih) / Math.min(bw / iw, bh / ih);
    }
    function applyFillZoom() {
      var zi = document.getElementById('hep-z');
      var z = Math.round(fillZoom(img) * 100);
      zi.value = Math.max(+zi.min, Math.min(+zi.max, z));
    }

    // Default to slide 2 if it exists
    if (imgs.length > 1) {
      img = imgs[1];
      activeIdx = 1;
      if (window._heroGoTo) window._heroGoTo(1);
    }

    var initPos = getPosFrom(img);
    var initX = initPos.x, initY = initPos.y;

    var slideOpts = Array.from(imgs).map(function(_, i) {
      return '<option value="' + i + '">Slide ' + (i + 1) + '</option>';
    }).join('');

    var panel = document.createElement('div');
    panel.id = 'hep';
    panel.innerHTML =
      '<div class="hep-title">Hero Image Editor</div>' +
      '<div class="hep-hint">Drag the image to move it, or use the sliders.</div>' +
      '<label>Slide <select id="hep-slide">' + slideOpts + '</select></label>' +
      '<label>X Position <span id="hep-xv">' + initX + '</span>%' +
        '<input type="range" id="hep-x" min="0" max="100" value="' + initX + '">' +
      '</label>' +
      '<label>Y Position <span id="hep-yv">' + initY + '</span>%' +
        '<input type="range" id="hep-y" min="0" max="100" value="' + initY + '">' +
      '</label>' +
      '<label>Zoom <span id="hep-zv">1.00</span>x' +
        '<input type="range" id="hep-z" min="30" max="260" value="100" step="1">' +
      '</label>' +
      '<div id="hep-out"></div>' +
      '<button id="hep-copy">Copy CSS (this slide)</button>' +
      '<button id="hep-copyall">Copy All Slides</button>' +
      '<div class="hep-count" id="hep-count">0 slides adjusted</div>';
    document.body.appendChild(panel);
    if (imgs.length > 1) document.getElementById('hep-slide').value = '1';

    var style = document.createElement('style');
    style.textContent = [
      '#hep{position:fixed;top:80px;right:12px;z-index:9999;background:rgba(0,0,0,.88);',
      'color:#fff;padding:14px;border-radius:12px;font:13px/1.5 system-ui;width:210px;',
      'box-shadow:0 4px 20px rgba(0,0,0,.5);}',
      '#hep .hep-title{font-weight:700;font-size:14px;margin-bottom:4px;}',
      '#hep .hep-hint{font-size:11px;opacity:.7;margin-bottom:10px;}',
      '.hep-on .hero-primary-media img{cursor:grab;}',
      '.hep-drag .hero-primary-media img{cursor:grabbing;}',
      '#hep label{display:block;margin-bottom:8px;}',
      '#hep input[type=range]{display:block;width:100%;margin-top:3px;accent-color:#D7392A;}',
      '#hep-out{font-size:11px;background:rgba(255,255,255,.12);padding:7px 9px;',
      'border-radius:7px;margin:10px 0;word-break:break-all;white-space:pre-line;line-height:1.6;}',
      '#hep-copy{width:100%;padding:7px;background:#D7392A;color:#fff;border:none;',
      'border-radius:7px;cursor:pointer;font-weight:700;font-size:13px;}',
      '#hep-copyall{width:100%;margin-top:6px;padding:7px;background:#1f2937;color:#fff;',
      'border:1px solid #374151;border-radius:7px;cursor:pointer;font-weight:700;font-size:13px;}',
      '#hep .hep-count{font-size:11px;opacity:.7;margin-top:6px;text-align:center;}',
      '#hep select{width:100%;margin-top:3px;background:#222;color:#fff;border:1px solid #555;',
      'border-radius:5px;padding:3px 6px;}'
    ].join('');
    document.head.appendChild(style);

    function update() {
      var x = +document.getElementById('hep-x').value;
      var y = +document.getElementById('hep-y').value;
      var z = document.getElementById('hep-z').value / 100;
      document.getElementById('hep-xv').textContent = x;
      document.getElementById('hep-yv').textContent = y;
      document.getElementById('hep-zv').textContent = z.toFixed(2);

      // Always contain + scale: the whole image is the reference, so zoom is a
      // single smooth axis. ~1.0 = whole image fits; zoom up to fill/crop, down to shrink.
      img.style.objectFit = 'contain';
      img.style.objectPosition = x + '% ' + y + '%';
      img.style.transformOrigin = x + '% ' + y + '%';
      img.style.transform = 'scale(' + z + ')';

      document.getElementById('hep-out').textContent =
        'object-fit: contain;\n' +
        'object-position: ' + x + '% ' + y + '%;\n' +
        'transform: scale(' + z.toFixed(2) + ');\n' +
        'transform-origin: ' + x + '% ' + y + '%;';
    }

    // Apply + remember this slide. Used only for real user edits (sliders / drag),
    // so slides you merely view aren't added to the export.
    function recordAndUpdate() {
      update();
      slideState[activeIdx] = {
        x: +document.getElementById('hep-x').value,
        y: +document.getElementById('hep-y').value,
        z: +document.getElementById('hep-z').value
      };
      var n = Object.keys(slideState).length;
      document.getElementById('hep-count').textContent =
        n + ' slide' + (n === 1 ? '' : 's') + ' adjusted';
    }

    ['hep-x', 'hep-y', 'hep-z'].forEach(function (id) {
      document.getElementById(id).addEventListener('input', recordAndUpdate);
    });

    // Drag anywhere on the hero to reposition the focal point of the active slide.
    document.body.classList.add('hep-on');
    var heroEl = document.getElementById('hero');
    var dragging = false, startX = 0, startY = 0, baseX = 0, baseY = 0;
    document.addEventListener('pointerdown', function (e) {
      if (!heroEl || !heroEl.contains(e.target)) return;
      if (e.target.closest('a, button, select, input, label')) return; // leave controls alone
      dragging = true;
      startX = e.clientX; startY = e.clientY;
      baseX = +document.getElementById('hep-x').value;
      baseY = +document.getElementById('hep-y').value;
      document.body.classList.add('hep-drag');
      e.preventDefault();
    });
    document.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      var rect = img.getBoundingClientRect();
      var gain = 1.3; // dragging the image moves it the same direction (invert object-position)
      var nx = Math.max(0, Math.min(100, baseX - (e.clientX - startX) / rect.width * 100 * gain));
      var ny = Math.max(0, Math.min(100, baseY - (e.clientY - startY) / rect.height * 100 * gain));
      document.getElementById('hep-x').value = Math.round(nx);
      document.getElementById('hep-y').value = Math.round(ny);
      recordAndUpdate();
    });
    document.addEventListener('pointerup', function () {
      dragging = false;
      document.body.classList.remove('hep-drag');
    });

    document.getElementById('hep-slide').addEventListener('change', function () {
      activeIdx = +this.value;
      img = imgs[activeIdx];
      // also navigate the carousel to that slide
      if (window._heroGoTo) window._heroGoTo(activeIdx);
      var st = slideState[activeIdx];
      if (st) { // restore this slide's previous edits
        document.getElementById('hep-x').value = st.x;
        document.getElementById('hep-y').value = st.y;
        document.getElementById('hep-z').value = st.z;
      } else {
        var p = getPosFrom(img);
        document.getElementById('hep-x').value = p.x;
        document.getElementById('hep-y').value = p.y;
        applyFillZoom();
      }
      update();
    });

    function buildRule(idx) {
      var st = slideState[idx];
      if (!st) return '';
      return '.hero-slide:nth-child(' + (idx + 1) + ') .hero-primary-media img {\n' +
             '  object-fit: contain;\n' +
             '  object-position: ' + st.x + '% ' + st.y + '%;\n' +
             '  transform: scale(' + (st.z / 100).toFixed(2) + ');\n' +
             '  transform-origin: ' + st.x + '% ' + st.y + '%;\n' +
             '}';
    }

    function copyText(text, btn, label) {
      function done() { btn.textContent = 'Copied!'; setTimeout(function () { btn.textContent = label; }, 1500); }
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(done);
      } else {
        var ta = document.createElement('textarea');
        ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
        document.body.appendChild(ta); ta.select(); document.execCommand('copy');
        document.body.removeChild(ta); done();
      }
    }

    document.getElementById('hep-copy').addEventListener('click', function () {
      copyText(document.getElementById('hep-out').textContent, this, 'Copy CSS (this slide)');
    });

    document.getElementById('hep-copyall').addEventListener('click', function () {
      var rules = Object.keys(slideState)
        .sort(function (a, b) { return a - b; })
        .map(function (k) { return buildRule(+k); })
        .filter(Boolean);
      copyText(rules.join('\n\n') || '/* adjust at least one slide first */', this, 'Copy All Slides');
    });

    if (img.complete && img.naturalWidth) {
      applyFillZoom();
    } else {
      img.addEventListener('load', function () { applyFillZoom(); update(); });
    }
    update();
  });
})();
