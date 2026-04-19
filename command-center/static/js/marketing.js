(function () {
  const state = {
    presets: null,
    content: [],
    filter: 'all',
    selected: new Set(),
    dryRunPassed: false,
  };

  const $ = (id) => document.getElementById(id);
  const tab = () => document.querySelector('.tab[data-tab="marketing"]');

  function log(msg, cls) {
    const el = $('mkt-activity-log');
    if (!el) return;
    const empty = el.querySelector('.mkt-log-empty');
    if (empty) empty.remove();
    const line = document.createElement('div');
    line.className = 'mkt-log-line' + (cls ? ' ' + cls : '');
    const ts = new Date().toLocaleTimeString();
    line.textContent = '[' + ts + '] ' + msg;
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;
  }

  async function loadPresets() {
    try {
      const res = await fetch('/api/marketing/presets');
      const data = await res.json();
      state.presets = data;
      const audSel = $('mkt-audience');
      audSel.innerHTML = '';
      Object.entries(data.audiences || {}).forEach(([k, v]) => {
        const opt = document.createElement('option');
        opt.value = k;
        opt.textContent = v.name || k;
        audSel.appendChild(opt);
      });
      const budSel = $('mkt-budget');
      budSel.innerHTML = '';
      Object.entries(data.budgets || {}).forEach(([k, v]) => {
        const opt = document.createElement('option');
        opt.value = k;
        opt.textContent = 'P' + v.daily_php + '/day';
        budSel.appendChild(opt);
      });
      if (audSel.options.length && !audSel.value) audSel.selectedIndex = 0;
      if (budSel.options.length) {
        const stdIdx = Array.from(budSel.options).findIndex(o => o.value === 'standard_100d');
        budSel.selectedIndex = stdIdx >= 0 ? stdIdx : 0;
      }
      updatePresetNotes();
    } catch (e) {
      log('Preset load failed: ' + e.message, 'err');
    }
  }

  function updatePresetNotes() {
    if (!state.presets) return;
    const audKey = $('mkt-audience').value;
    const budKey = $('mkt-budget').value;
    const aud = state.presets.audiences[audKey];
    const bud = state.presets.budgets[budKey];
    $('mkt-audience-note').textContent = aud ? (aud.notes || '') : '';
    $('mkt-budget-note').textContent = bud ? (bud.notes || '') : '';
  }

  async function loadContent() {
    try {
      const res = await fetch('/api/marketing/content');
      const data = await res.json();
      state.content = data || [];
      renderGrid();
    } catch (e) {
      log('Content load failed: ' + e.message, 'err');
    }
  }

  function renderGrid() {
    const grid = $('mkt-thumb-grid');
    const items = state.filter === 'all'
      ? state.content
      : state.content.filter(c => c.type === state.filter);
    if (!items.length) {
      grid.innerHTML = '<div class="mkt-empty">No content matches.</div>';
      return;
    }
    grid.innerHTML = '';
    items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'mkt-thumb' + (state.selected.has(item.path) ? ' selected' : '');
      card.dataset.path = item.path;
      const img = document.createElement('img');
      img.loading = 'lazy';
      img.src = '/api/images/' + item.path;
      img.alt = item.filename;
      card.appendChild(img);
      const meta = document.createElement('div');
      meta.className = 'mkt-thumb-meta';
      const modelTag = item.model && item.model !== 'unidentified' ? item.model : item.type;
      meta.textContent = modelTag;
      card.appendChild(meta);
      card.addEventListener('click', () => toggleSelect(item.path, card));
      grid.appendChild(card);
    });
  }

  function toggleSelect(path, card) {
    if (state.selected.has(path)) {
      state.selected.delete(path);
      card.classList.remove('selected');
    } else {
      state.selected.add(path);
      card.classList.add('selected');
    }
    $('mkt-selected-count').textContent = state.selected.size + ' selected';
    state.dryRunPassed = false;
    $('mkt-publish').disabled = true;
    $('mkt-publish').title = 'Dry-run first';
  }

  async function loadInsights() {
    try {
      const res = await fetch('/api/marketing/insights');
      const data = await res.json();
      renderInsights(data);
    } catch (e) {
      $('mkt-insights-body').innerHTML = '<div class="mkt-empty">Insights unavailable</div>';
    }
  }

  function renderInsights(data) {
    const body = $('mkt-insights-body');
    if (!data || data.error) {
      body.innerHTML = '<div class="mkt-empty">' + (data && data.error ? 'Insights error' : 'No insights yet') + '</div>';
      return;
    }
    const camp = data.campaign || {};
    const spend = parseFloat(camp.spend || 0);
    const impr = parseInt(camp.impressions || 0);
    const clicks = parseInt(camp.clicks || 0);
    const ctr = impr ? ((clicks / impr) * 100).toFixed(2) : '0.00';
    const ads = (data.ads || []).slice().sort((a, b) => (parseInt(b.impressions || 0)) - (parseInt(a.impressions || 0))).slice(0, 3);
    let html = '<div class="mkt-insights-totals">';
    html += '<div><span class="mkt-k">Spend</span><span class="mkt-v">P' + spend.toFixed(0) + '</span></div>';
    html += '<div><span class="mkt-k">Impr</span><span class="mkt-v">' + impr.toLocaleString() + '</span></div>';
    html += '<div><span class="mkt-k">Clicks</span><span class="mkt-v">' + clicks + '</span></div>';
    html += '<div><span class="mkt-k">CTR</span><span class="mkt-v">' + ctr + '%</span></div>';
    html += '</div>';
    if (ads.length) {
      html += '<div class="mkt-top-ads"><div class="mkt-k">Top ads</div>';
      ads.forEach(a => {
        html += '<div class="mkt-ad-row">' + (a.ad_name || a.ad_id) + ' -- ' + (a.impressions || 0) + ' impr</div>';
      });
      html += '</div>';
    }
    body.innerHTML = html;
  }

  async function stage(dryRun) {
    if (!state.selected.size) {
      log('Select at least one creative first.', 'err');
      return;
    }
    const caption = $('mkt-caption').value.trim();
    if (!caption) {
      log('Caption is required.', 'err');
      return;
    }
    const adsetName = $('mkt-adset-name').value.trim() || ('MKT ' + new Date().toISOString().slice(0, 16).replace('T', ' '));
    const audKey = $('mkt-audience').value;
    const budKey = $('mkt-budget').value;
    const bud = state.presets.budgets[budKey];
    const payload = {
      dry_run: dryRun,
      ad_set: {
        name: adsetName,
        targeting_preset: audKey,
        daily_budget_php: bud.daily_php,
        caption: caption,
        headline: $('mkt-headline').value.trim(),
        creatives: Array.from(state.selected).map(p => ({ image_path: p })),
      },
    };
    log((dryRun ? 'Dry-run' : 'PUBLISH') + ': ' + state.selected.size + ' creative(s), audience=' + audKey + ', budget=P' + bud.daily_php + '/day');
    $('mkt-stage').disabled = true;
    $('mkt-publish').disabled = true;
    try {
      const res = await fetch('/api/marketing/stage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (data.stdout) {
        data.stdout.split('\n').filter(l => l.trim()).slice(-20).forEach(l => log(l));
      }
      if (data.stderr && data.stderr.trim()) {
        data.stderr.split('\n').filter(l => l.trim()).forEach(l => log('stderr: ' + l, 'err'));
      }
      if (data.ok) {
        if (dryRun) {
          state.dryRunPassed = true;
          $('mkt-publish').disabled = false;
          $('mkt-publish').title = 'Ready to publish (PAUSED)';
          log('Dry-run OK. Publish unlocked.', 'ok');
          if (window.showToast) window.showToast('Dry-run passed', 'success');
        } else {
          log('Staged PAUSED. Check Ads Manager.', 'ok');
          if (window.showToast) window.showToast('Ads staged (PAUSED)', 'success');
          state.dryRunPassed = false;
        }
      } else {
        log('Stage failed (exit=' + data.exit + ')', 'err');
        if (window.showToast) window.showToast('Stage failed', 'error');
      }
    } catch (e) {
      log('Request error: ' + e.message, 'err');
    } finally {
      $('mkt-stage').disabled = false;
      $('mkt-publish').disabled = !state.dryRunPassed;
    }
  }

  function wire() {
    $('mkt-audience').addEventListener('change', updatePresetNotes);
    $('mkt-budget').addEventListener('change', updatePresetNotes);
    tab().querySelectorAll('.mkt-filter-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        tab().querySelectorAll('.mkt-filter-pill').forEach(p => p.classList.remove('selected'));
        pill.classList.add('selected');
        state.filter = pill.dataset.filter;
        renderGrid();
      });
    });
    $('mkt-stage').addEventListener('click', () => stage(true));
    $('mkt-publish').addEventListener('click', () => {
      if (!state.dryRunPassed) return;
      if (!confirm('Stage ' + state.selected.size + ' ad(s) to Meta as PAUSED?')) return;
      stage(false);
    });
  }

  let initialized = false;
  function init() {
    if (initialized) return;
    initialized = true;
    wire();
    loadPresets();
    loadContent();
    loadInsights();
  }

  document.addEventListener('DOMContentLoaded', () => {
    const onHash = () => {
      if (window.location.hash === '#marketing' || (!window.location.hash && tab().classList.contains('active'))) {
        init();
      }
    };
    window.addEventListener('hashchange', onHash);
    onHash();
  });
})();
