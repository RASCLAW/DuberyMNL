// Marketing tab: analytics dashboard + staging UI (collapsed).
// Analytics: single fetch -> /api/marketing/summary populates every section.
//            Refresh button POSTs /api/marketing/refresh, then re-fetches summary.
// Staging:   unchanged from previous version, kept inside <details>.
(function () {
  "use strict";

  // ---------- shared helpers ----------
  const $ = (id) => document.getElementById(id);
  function setText(sel, txt) {
    document.querySelectorAll(`[data-mkt="${sel}"]`).forEach(el => { el.textContent = txt; });
  }
  function fmtMoney(n) {
    if (n === null || n === undefined) return "--";
    try { return "₱" + Number(n).toLocaleString("en-PH", { maximumFractionDigits: 0 }); }
    catch (e) { return String(n); }
  }
  function fmtMoneyDec(n) {
    if (n === null || n === undefined) return "--";
    return "₱" + Number(n).toFixed(2);
  }
  function fmtNum(n) {
    if (n === null || n === undefined) return "--";
    return Number(n).toLocaleString("en-PH");
  }
  function fmtPct(n) {
    if (n === null || n === undefined) return "--";
    return Number(n).toFixed(2) + "%";
  }
  function esc(s) {
    if (s === null || s === undefined) return "";
    return String(s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function timeAgo(iso) {
    if (!iso) return "no cache yet";
    const t = new Date(iso).getTime();
    if (!t) return iso;
    const m = Math.floor((Date.now() - t) / 60000);
    if (m < 1) return "just now";
    if (m < 60) return m + "m ago";
    const h = Math.floor(m / 60);
    if (h < 24) return h + "h ago";
    return Math.floor(h / 24) + "d ago";
  }

  // ---------- analytics state ----------
  const A = {
    summary: null,
    sort: { col: "cost_per_lpv", dir: "asc" },
    activeOnly: true,
  };

  function statusPill(s) {
    const cls = (s === "ACTIVE") ? "ok"
      : (s === "PAUSED") ? "gray"
      : "bad";
    const label = (s === "ACTIVE") ? "Active"
      : (s === "PAUSED") ? "Paused"
      : (s ? (s.charAt(0) + s.slice(1).toLowerCase()) : "—");
    return `<span class="pill ${cls}">${esc(label)}</span>`;
  }

  function ctrClass(ctr, avg) {
    if (!avg) return "";
    if (ctr >= avg * 1.25) return "ok";
    if (ctr <= avg * 0.6) return "bad";
    if (ctr < avg * 0.85) return "warn";
    return "";
  }

  function costLpvClass(cpl, avg) {
    if (!avg || cpl === null || cpl === undefined) return "";
    if (cpl <= avg * 0.75) return "ok";
    if (cpl >= avg * 1.4) return "bad";
    if (cpl >= avg * 1.15) return "warn";
    return "";
  }

  // Per-ad glanceable verdict from the same CTR + Cost/LPV signals the cell
  // coloring uses, plus the backend's pause floor (CTR < 1% on real spend).
  // avgCtr / avgCpl are the displayed-pool baselines computed in renderAds.
  function verdict(a, avgCtr, avgCpl) {
    const spend = a.spend || 0, ctr = a.ctr || 0, lpv = a.lpv || 0;
    const cpl = a.cost_per_lpv;
    if (spend < 20 || lpv < 3) return { word: "Learning", cls: "gray" };
    const cplBad  = avgCpl && cpl != null && cpl >= avgCpl * 1.40;
    const cplWarn = avgCpl && cpl != null && cpl >= avgCpl * 1.15;
    const cplGood = avgCpl && cpl != null && cpl <= avgCpl * 0.75;
    const ctrGood = avgCtr && ctr >= avgCtr * 1.25;
    const ctrBad  = avgCtr && ctr <= avgCtr * 0.60;
    if ((ctr < 1.0 && spend > 20) || cplBad) return { word: "Pause", cls: "bad" };
    if (ctrGood && (cplGood || !avgCpl))      return { word: "Winner", cls: "ok" };
    if (ctrBad || cplWarn)                    return { word: "Watch", cls: "warn" };
    return { word: "Solid", cls: "accent" };
  }

  // ---------- render: snapshot ----------
  function renderSnapshot(snap) {
    if (!snap) {
      setText("snap_spend", "--");
      setText("snap_spend_sub", "no data");
      return;
    }
    setText("snap_spend", fmtMoney(snap.spend));
    setText("snap_spend_sub", "~" + fmtMoney(snap.spend_per_day) + "/day avg");
    setText("snap_impr", fmtNum(snap.impressions));
    setText("snap_cpm", snap.cpm ? "CPM " + fmtMoneyDec(snap.cpm) : "—");
    setText("snap_clicks", fmtNum(snap.clicks));
    setText("snap_cpc", snap.cpc ? "CPC " + fmtMoneyDec(snap.cpc) : "—");
    setText("snap_lpv", fmtNum(snap.lpv));
    setText("snap_cost_lpv", snap.cost_per_lpv ? "Cost / LPV " + fmtMoneyDec(snap.cost_per_lpv) : "—");
    setText("snap_msgs", fmtNum(snap.messages));
    setText("snap_purchases", fmtNum(snap.purchases_pixel));
  }

  // ---------- render: adsets ----------
  function renderAdsets(adsets) {
    const tbody = document.querySelector('[data-mkt="adsets_tbody"]');
    if (!tbody) return;
    if (!adsets || !adsets.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="muted" style="text-align:center;padding:18px;">No adsets in cache. Click Refresh.</td></tr>';
      return;
    }
    const avgCtr = adsets.reduce((s, a) => s + (a.ctr || 0), 0) / adsets.length;
    tbody.innerHTML = adsets.map(a => `
      <tr${a.status === "ACTIVE" ? "" : ' class="dim"'}>
        <td><span class="tname">${esc(a.name)}<span class="tsub">${esc(a.adset_id)}</span></span></td>
        <td>${statusPill(a.status)}</td>
        <td class="num">${a.daily_budget_php != null ? "<b>" + fmtMoney(a.daily_budget_php) + "</b>" : "—"}</td>
        <td class="num">${fmtMoney(a.spend)}</td>
        <td class="num ${ctrClass(a.ctr, avgCtr)}">${fmtPct(a.ctr)}</td>
        <td class="num">${a.cost_per_lpv ? fmtMoneyDec(a.cost_per_lpv) : "—"}</td>
        <td class="num">${fmtNum(a.lpv)}</td>
        <td class="num">${fmtNum(a.messages)}</td>
      </tr>
    `).join("");
  }

  // ---------- render: ads leaderboard ----------
  function sortAds(ads) {
    const { col, dir } = A.sort;
    const sign = dir === "desc" ? -1 : 1;
    return [...ads].sort((a, b) => {
      let av = a[col], bv = b[col];
      if (typeof av === "string") return sign * av.localeCompare(bv || "");
      av = (av == null) ? -Infinity : av;
      bv = (bv == null) ? -Infinity : bv;
      return sign * (av - bv);
    });
  }

  function renderAds(ads) {
    const tbody = document.querySelector('[data-mkt="ads_tbody"]');
    if (!tbody) return;
    let pool = ads || [];
    if (A.activeOnly) pool = pool.filter(a => a.status === "ACTIVE");
    pool = pool.filter(a => (a.spend || 0) > 0);
    if (!pool.length) {
      tbody.innerHTML = '<tr><td colspan="10" class="muted" style="text-align:center;padding:18px;">No ads to show. Click Refresh.</td></tr>';
      return;
    }
    // Average baselines for color coding
    const avgCtr = pool.reduce((s, a) => s + (a.ctr || 0), 0) / pool.length;
    const cplVals = pool.filter(a => a.cost_per_lpv).map(a => a.cost_per_lpv);
    const avgCpl = cplVals.length ? cplVals.reduce((s, v) => s + v, 0) / cplVals.length : null;
    const sorted = sortAds(pool);
    tbody.innerHTML = sorted.map(a => {
      const thumb = a.thumbnail_url
        ? `<span class="thumb"><img src="${esc(a.thumbnail_url)}" alt="" loading="lazy" style="width:100%;height:100%;object-fit:cover"></span>`
        : `<span class="thumb"></span>`;
      const v = verdict(a, avgCtr, avgCpl);
      const vWhy = `CTR ${fmtPct(a.ctr)} · Cost/LPV ${a.cost_per_lpv ? fmtMoneyDec(a.cost_per_lpv) : "—"} · ${fmtNum(a.lpv)} LPV`;
      return `
      <tr${a.status === "ACTIVE" ? "" : ' class="dim"'}>
        <td>
          <div style="display:flex; gap:10px; align-items:center">
            ${thumb}
            <span class="tname">${esc(a.name)}<span class="tsub">${esc(a.adset_name)} · ${esc(a.ad_id)}</span></span>
          </div>
        </td>
        <td>${statusPill(a.status)}</td>
        <td><span class="pill ${v.cls}" title="${esc(vWhy)}">${v.word}</span></td>
        <td class="num">${fmtMoney(a.spend)}</td>
        <td class="num">${fmtNum(a.impressions)}</td>
        <td class="num ${ctrClass(a.ctr, avgCtr)}">${fmtPct(a.ctr)}</td>
        <td class="num">${fmtNum(a.lpv)}</td>
        <td class="num ${costLpvClass(a.cost_per_lpv, avgCpl)}">${a.cost_per_lpv ? fmtMoneyDec(a.cost_per_lpv) : "—"}</td>
        <td class="num">${fmtNum(a.messages)}</td>
        <td class="num">${fmtNum(a.purchases)}</td>
      </tr>`;
    }).join("");
    // Update sort indicators
    document.querySelectorAll('.mkt-ads-table th[data-sort]').forEach(th => {
      th.classList.remove('sorted-asc', 'sorted-desc');
      if (th.dataset.sort === A.sort.col) {
        th.classList.add(A.sort.dir === 'asc' ? 'sorted-asc' : 'sorted-desc');
      }
    });
  }

  // ---------- render: pixel funnel ----------
  // Emits the redesign .funnel / .frow / .fdrop markup into [data-mkt="pixel_grid"]
  // (the container is now a .funnel div). Bar widths are inline because the
  // .fbar.v* fill widths the static mockup used are not in main.css.
  function renderPixel(pixel, gap) {
    const grid = document.querySelector('[data-mkt="pixel_grid"]');
    if (!grid) return;
    if (!pixel || !pixel.events || !pixel.events.length) {
      grid.innerHTML = '<div class="muted small" style="padding:14px;">No pixel data cached. Click Refresh.</div>';
    } else {
      setText("pixel_window", `Pixel ${pixel.pixel_id} · last ${pixel.days} days`);
      // bar fill color per event (PageView baseline -> Purchase = leak/bad)
      const evFill = { PageView: "#cdbfae", ViewContent: "var(--accent)", AddToCart: "var(--warn)", Purchase: "var(--bad)" };
      const base = pixel.events[0] ? pixel.events[0].count : 0;
      let html = "";
      pixel.events.forEach((e, i) => {
        const fill = evFill[e.name] || "#cdbfae";
        const w = base ? Math.max(0.6, Math.min(100, (e.count / base) * 100)) : 0;
        html += `
          <div class="frow">
            <span class="flabel">${esc(e.name)}</span>
            <div class="fbar"><i style="width:${w.toFixed(2)}%; background:${fill};"></i></div>
            <span class="fnum">${fmtNum(e.count)}</span>
          </div>`;
        // step-down rate between this event and the next
        const next = pixel.events[i + 1];
        if (next) {
          const stepPct = e.count ? (next.count / e.count) * 100 : 0;
          const crit = next.name === "Purchase";
          html += `
          <div class="fdrop${crit ? " crit" : ""}"><span></span><span>&#8595; ${stepPct.toFixed(1)}%${crit ? " &#8212; the leak lives here" : ""}</span></div>`;
        }
      });
      grid.innerHTML = html;
    }

    // Gap callout
    const cal = document.querySelector('[data-mkt="gap_callout"]');
    if (!cal) return;
    if (gap && gap.unattributed > 0) {
      cal.classList.remove("hidden");
      setText("gap_sheet", fmtNum(gap.sheet_orders));
      setText("gap_pixel", fmtNum(gap.pixel_purchases));
      setText("gap_num", fmtNum(gap.unattributed));
      setText("gap_title", `Pixel gap — ${gap.unattributed} of ${gap.sheet_orders} orders are unattributed`);
      setText("gap_explain", "COD checkout confirms off-page, so most purchases never hit the pixel. Most likely organic / direct / Messenger traffic. The utm_content={{ad.id}} wiring (active 2026-05-25) narrows this for ad-driven orders going forward. Trust the sheet, not the pixel.");
    } else {
      cal.classList.add("hidden");
    }
  }

  // ---------- render: daily trend (SVG) ----------
  function renderTrend(days) {
    const svg = document.querySelector('[data-mkt="trend_svg"]');
    const note = document.querySelector('[data-mkt="trend_note"]');
    if (!svg) return;
    if (!days || !days.length) {
      svg.innerHTML = '<text x="350" y="100" text-anchor="middle" fill="#9e9890" font-size="11">No daily data cached. Click Refresh.</text>';
      if (note) note.textContent = "—";
      return;
    }
    const W = 700, H = 200, P_L = 44, P_R = 14, P_T = 14, P_B = 30;
    const innerW = W - P_L - P_R;
    const innerH = H - P_T - P_B;

    const spends = days.map(d => d.spend);
    const lpvs = days.map(d => d.lpv);
    const ctrs = days.map(d => d.ctr);
    const maxSpend = Math.max(...spends, 1);
    const maxLpv = Math.max(...lpvs, 1);
    const maxCtr = Math.max(...ctrs, 1);

    const x = (i) => P_L + (i / Math.max(1, days.length - 1)) * innerW;
    const ySpend = (v) => P_T + innerH - (v / maxSpend) * innerH;
    const yLpv = (v) => P_T + innerH - (v / maxLpv) * innerH;
    const yCtr = (v) => P_T + innerH - (v / maxCtr) * innerH;

    const pts = (yFn, arr) => arr.map((v, i) => `${x(i).toFixed(1)},${yFn(v).toFixed(1)}`).join(" ");

    // Gridlines & y labels (use spend scale for primary axis)
    const ticks = 4;
    let grid = "";
    for (let t = 0; t <= ticks; t++) {
      const yy = P_T + (innerH * t / ticks);
      const val = Math.round(maxSpend * (1 - t / ticks));
      grid += `<line x1="${P_L}" y1="${yy}" x2="${W - P_R}" y2="${yy}" stroke="#e5ddd3" stroke-width="1" stroke-dasharray="2,2"/>`;
      grid += `<text x="${P_L - 6}" y="${yy + 3}" text-anchor="end" fill="#6b6560" font-size="9" font-family="ui-monospace,monospace">${val}</text>`;
    }

    // X labels (every other day to avoid clutter)
    let xlabels = "";
    days.forEach((d, i) => {
      if (days.length <= 8 || i % 2 === 0 || i === days.length - 1) {
        xlabels += `<text x="${x(i)}" y="${H - 10}" text-anchor="middle" fill="#6b6560" font-size="9" font-family="ui-monospace,monospace">${d.date.slice(8)}</text>`;
      }
    });

    const lastIdx = days.length - 1;

    svg.innerHTML = `
      ${grid}
      ${xlabels}
      <polyline fill="none" stroke="#e07a3a" stroke-width="2" points="${pts(ySpend, spends)}"/>
      <polyline fill="none" stroke="#2d8a4e" stroke-width="2" points="${pts(yLpv, lpvs)}"/>
      <polyline fill="none" stroke="#b8860b" stroke-width="2" stroke-dasharray="3,3" points="${pts(yCtr, ctrs)}"/>
      <circle cx="${x(lastIdx)}" cy="${ySpend(spends[lastIdx])}" r="3.5" fill="#e07a3a"/>
      <circle cx="${x(lastIdx)}" cy="${yLpv(lpvs[lastIdx])}" r="3.5" fill="#2d8a4e"/>
    `;

    if (note && days.length >= 2) {
      const recent = days.slice(-3).reduce((s, d) => s + d.spend, 0) / Math.min(3, days.length);
      const prior = days.slice(0, 3).reduce((s, d) => s + d.spend, 0) / Math.min(3, days.length);
      const trend = recent > prior * 1.1 ? "↗ Spend trending up"
                  : recent < prior * 0.9 ? "↘ Spend trending down"
                  : "→ Spend roughly flat";
      const lastDate = days[days.length - 1].date;
      note.textContent = `${trend} (recent 3-day avg ${fmtMoneyDec(recent)} vs first 3-day avg ${fmtMoneyDec(prior)}). Last point: ${lastDate}.`;
    }
  }

  // ---------- render: needs attention ----------
  function renderAttention(items) {
    const wrap = document.querySelector('[data-mkt="attention_list"]');
    if (!wrap) return;
    if (!items || !items.length) {
      wrap.innerHTML = '<div class="muted small" style="padding:8px 0;">Nothing flagged. All quiet.</div>';
      return;
    }
    wrap.innerHTML = items.map(item => {
      const cls = item.tone === "ok" ? "ok"
                : item.tone === "warn" ? "warn"
                : "bad";
      const head = item.ad_name ? esc(item.ad_name) : esc(item.label);
      const sub = [item.ad_name ? esc(item.label) : "", esc(item.detail), esc(item.value)]
        .filter(Boolean).join(" · ");
      const pillWord = item.tone === "ok" ? "Good"
                     : item.tone === "warn" ? "Watch"
                     : "Pause";
      return `
        <div class="rail-item">
          <span class="label">${head}<span class="sub">${sub}</span></span>
          <span class="pill ${cls}" style="margin-left:auto">${pillWord}</span>
        </div>
      `;
    }).join("");
  }

  // ---------- fetch summary ----------
  async function fetchSummary() {
    try {
      const res = await fetch("/api/marketing/summary", { cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const d = await res.json();
      A.summary = d;

      // meta bar + cache age
      const win = d.window || {};
      const winText = (win.from && win.to) ? `${win.from} → ${win.to}` : "no window";
      setText("meta_bar", `Window: 7d · Account: ${win.campaign_id || "—"} · Pixel: ${(d.pixel && d.pixel.pixel_id) || "—"} · ${winText}`);
      const cache = d.cache || {};
      const oldest = [cache.insights_mtime, cache.live_meta_mtime, cache.pixel_mtime, cache.daily_mtime]
        .filter(Boolean).sort()[0];
      setText("cache_age", "data: " + timeAgo(oldest));

      renderSnapshot(d.snapshot);
      renderAdsets(d.adsets);
      renderAds(d.ads);
      renderPixel(d.pixel, d.gap);
      renderTrend(d.daily);
      renderAttention(d.needs_attention);
    } catch (e) {
      setText("cache_age", "fetch failed: " + e.message);
    }
  }

  async function fetchPageAnalytics() {
    try {
      const res = await fetch("/api/analytics/page", { cache: "no-store" });
      if (!res.ok) return;
      const d = await res.json();
      setText("page_fans", fmtNum((d.fans || {}).total));
      setText("page_talking", fmtNum((d.talking_about || {}).total));
      setText("page_impr", fmtNum((d.page_impressions_unique || {}).total));
      setText("page_eng", fmtNum((d.page_post_engagements || {}).total));
      setText("page_views", fmtNum((d.page_views_total || {}).total));
    } catch (e) { /* best-effort */ }
  }

  // ---------- refresh action ----------
  async function refreshAll() {
    const btn = $("mkt-refresh-btn");
    if (btn) { btn.disabled = true; btn.textContent = "Refreshing…"; }
    setText("cache_age", "refreshing…");
    try {
      const res = await fetch("/api/marketing/refresh", { method: "POST" });
      const d = await res.json();
      if (!d.ok) {
        const failed = Object.entries(d.steps || {}).filter(([_, s]) => !s.ok)
          .map(([k, s]) => `${k}: ${s.stderr || "exit " + s.exit}`).join(" | ");
        setText("cache_age", "partial refresh failure — " + failed.slice(0, 200));
      }
      await fetchSummary();
      await fetchPageAnalytics();
    } catch (e) {
      setText("cache_age", "refresh failed: " + e.message);
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "↻ Refresh"; }
    }
  }

  // ---------- sort wiring ----------
  function wireSorting() {
    document.querySelectorAll('.mkt-ads-table th[data-sort]').forEach(th => {
      th.addEventListener('click', () => {
        const col = th.dataset.sort;
        if (A.sort.col === col) {
          A.sort.dir = (A.sort.dir === 'asc') ? 'desc' : 'asc';
        } else {
          A.sort.col = col;
          // Cost per LPV defaults ascending (cheapest first); everything else descending.
          A.sort.dir = (col === 'cost_per_lpv' || col === 'name') ? 'asc' : 'desc';
        }
        if (A.summary) renderAds(A.summary.ads);
      });
    });
  }

  // ====================== STAGING UI (preserved) ======================
  // Unchanged behavior from previous version, just wrapped inside the
  // collapsed <details>. Initialized lazily when staging is first opened.

  const S = {
    presets: null,
    content: [],
    filter: 'all',
    selected: new Set(),
    dryRunPassed: false,
    initialized: false,
  };

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
      S.presets = data;
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
        opt.textContent = '₱' + v.daily_php + '/day';
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
    if (!S.presets) return;
    const audKey = $('mkt-audience').value;
    const budKey = $('mkt-budget').value;
    const aud = S.presets.audiences[audKey];
    const bud = S.presets.budgets[budKey];
    $('mkt-audience-note').textContent = aud ? (aud.notes || '') : '';
    $('mkt-budget-note').textContent = bud ? (bud.notes || '') : '';
  }

  async function loadContent() {
    try {
      const res = await fetch('/api/marketing/content');
      const data = await res.json();
      S.content = data || [];
      renderGrid();
    } catch (e) {
      log('Content load failed: ' + e.message, 'err');
    }
  }

  function renderGrid() {
    const grid = $('mkt-thumb-grid');
    const items = S.filter === 'all'
      ? S.content
      : S.content.filter(c => c.type === S.filter);
    if (!items.length) {
      grid.innerHTML = '<div class="mkt-empty">No content matches.</div>';
      return;
    }
    grid.innerHTML = '';
    items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'mkt-thumb' + (S.selected.has(item.path) ? ' selected' : '');
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
    if (S.selected.has(path)) {
      S.selected.delete(path);
      card.classList.remove('selected');
    } else {
      S.selected.add(path);
      card.classList.add('selected');
    }
    $('mkt-selected-count').textContent = S.selected.size + ' selected';
    S.dryRunPassed = false;
    $('mkt-publish').disabled = true;
    $('mkt-publish').title = 'Dry-run first';
  }

  async function stage(dryRun) {
    if (!S.selected.size) {
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
    const bud = S.presets.budgets[budKey];
    const payload = {
      dry_run: dryRun,
      ad_set: {
        name: adsetName,
        targeting_preset: audKey,
        daily_budget_php: bud.daily_php,
        caption: caption,
        headline: $('mkt-headline').value.trim(),
        creatives: Array.from(S.selected).map(p => ({ image_path: p })),
      },
    };
    log((dryRun ? 'Dry-run' : 'PUBLISH') + ': ' + S.selected.size + ' creative(s), audience=' + audKey + ', budget=₱' + bud.daily_php + '/day');
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
          S.dryRunPassed = true;
          $('mkt-publish').disabled = false;
          $('mkt-publish').title = 'Ready to publish (PAUSED)';
          log('Dry-run OK. Publish unlocked.', 'ok');
          if (window.showToast) window.showToast('Dry-run passed', 'success');
        } else {
          log('Staged PAUSED. Check Ads Manager.', 'ok');
          if (window.showToast) window.showToast('Ads staged (PAUSED)', 'success');
          S.dryRunPassed = false;
        }
      } else {
        log('Stage failed (exit=' + data.exit + ')', 'err');
        if (window.showToast) window.showToast('Stage failed', 'error');
      }
    } catch (e) {
      log('Request error: ' + e.message, 'err');
    } finally {
      $('mkt-stage').disabled = false;
      $('mkt-publish').disabled = !S.dryRunPassed;
    }
  }

  function initStaging() {
    if (S.initialized) return;
    S.initialized = true;
    const tab = document.querySelector('.tab[data-tab="marketing"]');
    tab.querySelectorAll('.mkt-filter-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        tab.querySelectorAll('.mkt-filter-pill').forEach(p => p.classList.remove('selected'));
        pill.classList.add('selected');
        S.filter = pill.dataset.filter;
        renderGrid();
      });
    });
    $('mkt-audience').addEventListener('change', updatePresetNotes);
    $('mkt-budget').addEventListener('change', updatePresetNotes);
    $('mkt-stage').addEventListener('click', () => stage(true));
    $('mkt-publish').addEventListener('click', () => {
      if (!S.dryRunPassed) return;
      if (!confirm('Stage ' + S.selected.size + ' ad(s) to Meta as PAUSED?')) return;
      stage(false);
    });
    loadPresets();
    loadContent();
  }

  // ---------- init ----------
  let analyticsInitialized = false;
  function init() {
    if (analyticsInitialized) return;
    analyticsInitialized = true;
    wireSorting();
    $("mkt-refresh-btn").addEventListener("click", refreshAll);
    const details = $("mkt-staging-details");
    if (details) details.addEventListener("toggle", () => {
      if (details.open) initStaging();
    });
    fetchSummary();
    fetchPageAnalytics();
  }

  document.addEventListener("tab:activated", ev => {
    if (ev.detail && ev.detail.tab === "marketing") init();
  });

  // Fallback for hash-routed navigation
  document.addEventListener('DOMContentLoaded', () => {
    const tab = document.querySelector('.tab[data-tab="marketing"]');
    if (tab && tab.classList.contains('active')) init();
    if (window.location.hash === '#marketing') init();
  });
})();
