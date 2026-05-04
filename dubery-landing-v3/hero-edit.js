(function () {
  if (!location.search.includes('edit')) return;

  document.addEventListener('DOMContentLoaded', function () {
    var imgs = document.querySelectorAll('.hero-primary-media img');
    if (!imgs.length) return;
    var img = imgs[0];

    function getPosFrom(el) {
      var computed = getComputedStyle(el);
      var pos = (computed.objectPosition || '49% 44%').split(' ');
      return { x: parseFloat(pos[0]) || 49, y: parseFloat(pos[1]) || 44 };
    }

    // Default to slide 2 if it exists
    if (imgs.length > 1) {
      img = imgs[1];
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
      '<label>Slide <select id="hep-slide">' + slideOpts + '</select></label>' +
      '<label>X Position <span id="hep-xv">' + initX + '</span>%' +
        '<input type="range" id="hep-x" min="0" max="100" value="' + initX + '">' +
      '</label>' +
      '<label>Y Position <span id="hep-yv">' + initY + '</span>%' +
        '<input type="range" id="hep-y" min="0" max="100" value="' + initY + '">' +
      '</label>' +
      '<label>Zoom <span id="hep-zv">1.0</span>x' +
        '<input type="range" id="hep-z" min="50" max="250" value="100" step="5">' +
      '</label>' +
      '<div id="hep-out"></div>' +
      '<button id="hep-copy">Copy CSS</button>';
    document.body.appendChild(panel);
    if (imgs.length > 1) document.getElementById('hep-slide').value = '1';

    var style = document.createElement('style');
    style.textContent = [
      '#hep{position:fixed;top:80px;right:12px;z-index:9999;background:rgba(0,0,0,.88);',
      'color:#fff;padding:14px;border-radius:12px;font:13px/1.5 system-ui;width:210px;',
      'box-shadow:0 4px 20px rgba(0,0,0,.5);}',
      '#hep .hep-title{font-weight:700;font-size:14px;margin-bottom:10px;}',
      '#hep label{display:block;margin-bottom:8px;}',
      '#hep input[type=range]{display:block;width:100%;margin-top:3px;accent-color:#D7392A;}',
      '#hep-out{font-size:11px;background:rgba(255,255,255,.12);padding:7px 9px;',
      'border-radius:7px;margin:10px 0;word-break:break-all;white-space:pre-line;line-height:1.6;}',
      '#hep-copy{width:100%;padding:7px;background:#D7392A;color:#fff;border:none;',
      'border-radius:7px;cursor:pointer;font-weight:700;font-size:13px;}',
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
      document.getElementById('hep-zv').textContent = z.toFixed(1);

      img.style.objectPosition = x + '% ' + y + '%';
      img.style.transformOrigin = x + '% ' + y + '%';
      img.style.transform = z > 1 ? 'scale(' + z + ')' : '';

      var out = 'object-position: ' + x + '% ' + y + '%;';
      if (z > 1) out += '\ntransform: scale(' + z.toFixed(2) + ');\ntransform-origin: ' + x + '% ' + y + '%;';
      document.getElementById('hep-out').textContent = out;
    }

    ['hep-x', 'hep-y', 'hep-z'].forEach(function (id) {
      document.getElementById(id).addEventListener('input', update);
    });

    document.getElementById('hep-slide').addEventListener('change', function () {
      img = imgs[+this.value];
      // also navigate the carousel to that slide
      if (window._heroGoTo) window._heroGoTo(+this.value);
      var p = getPosFrom(img);
      document.getElementById('hep-x').value = p.x;
      document.getElementById('hep-y').value = p.y;
      document.getElementById('hep-z').value = 100;
      update();
    });

    document.getElementById('hep-copy').addEventListener('click', function () {
      var btn = this;
      var text = document.getElementById('hep-out').textContent;
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function () {
          btn.textContent = 'Copied!';
          setTimeout(function () { btn.textContent = 'Copy CSS'; }, 1500);
        });
      } else {
        // fallback for older mobile browsers
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        btn.textContent = 'Copied!';
        setTimeout(function () { btn.textContent = 'Copy CSS'; }, 1500);
      }
    });

    update();
  });
})();
