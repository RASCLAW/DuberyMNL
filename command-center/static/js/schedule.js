// Schedule tab: queue feed posts to the FB Page.
(function () {
  "use strict";

  const TAB = "schedule";
  const LAYOUT_NEEDS = { "2h": 2, "2v": 2, "1p2": 3, "2x2": 4, "3h": 3, "hero3": 4, "ba": 2 };
  const MAX_IMAGES = 10;
  const POLL_MS = 30000;

  const state = {
    images: [], // array of {path, src_url, filename}
    mode: "multi",
    layout: "2h",
    bankItems: [],
    bankFilter: "all",
    bankSearch: "",
    pollTimer: null,
    activated: false,
    previewTimer: null,
  };

  // ---- helpers ----
  const $ = (id) => document.getElementById(id);

  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  }

  function toast(msg, kind) {
    if (window.__toast) window.__toast(msg, kind);
    else console.log("[schedule]", msg);
  }

  function fmtPHT(iso) {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      return d.toLocaleString("en-PH", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit", hour12: true, timeZone: "Asia/Manila" });
    } catch (e) { return iso; }
  }

  function relTime(iso) {
    if (!iso) return "";
    const target = new Date(iso).getTime();
    const now = Date.now();
    const diff = target - now;
    const past = diff < 0;
    const abs = Math.abs(diff);
    const min = Math.round(abs / 60000);
    const hr = Math.round(min / 60);
    const day = Math.round(hr / 24);
    let s;
    if (min < 1) s = past ? "just now" : "any moment";
    else if (min < 60) s = `${min}m`;
    else if (hr < 24) s = `${hr}h ${min % 60}m`;
    else s = `${day}d ${hr % 24}h`;
    return past ? `${s} ago` : `in ${s}`;
  }

  function localIsoNow(offsetMin) {
    const d = new Date(Date.now() + offsetMin * 60000);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const hh = String(d.getHours()).padStart(2, "0");
    const mi = String(d.getMinutes()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}T${hh}:${mi}`;
  }

  function datetimeLocalToPhtIso(value) {
    if (!value) return "";
    // value: "YYYY-MM-DDTHH:MM" interpreted as PHT (assume user is in PHT)
    return `${value}:00+08:00`;
  }

  // ---- queue render ----
  async function fetchQueue() {
    try {
      const [q, lr] = await Promise.all([
        fetch("/api/schedule/queue").then(r => r.json()),
        fetch("/api/schedule/last-run").then(r => r.json()),
      ]);
      renderQueue(q);
      renderWorkerStatus(lr);
    } catch (e) {
      console.error("fetchQueue failed", e);
    }
  }

  function renderWorkerStatus(lr) {
    const txt = $("schedWorkerStatusText");
    const dot = document.querySelector("#schedWorkerStatus .sched-worker-dot");
    if (!txt) return;
    if (!lr || !lr.last_run_at) {
      txt.textContent = "Worker has not run yet";
      if (dot) dot.classList.add("stale");
      return;
    }
    const rel = relTime(lr.last_run_at);
    const counts = `posted ${lr.posted || 0}, failed ${lr.failed || 0}`;
    txt.innerHTML = `Worker last ran <strong>${escapeHtml(rel)}</strong> &middot; ${escapeHtml(counts)}`;
    const ageMin = (Date.now() - new Date(lr.last_run_at).getTime()) / 60000;
    if (dot) dot.classList.toggle("stale", ageMin > 80);
  }

  function renderQueue(data) {
    renderCol("schedColUpcoming", "schedCountUpcoming", data.upcoming || [], "upcoming");
    renderCol("schedColPosted", "schedCountPosted", data.posted || [], "posted");
    renderCol("schedColFailed", "schedCountFailed", data.failed || [], "failed");
  }

  function renderCol(colId, countId, items, kind) {
    const col = $(colId);
    const count = $(countId);
    if (!col) return;
    if (count) count.textContent = items.length;
    if (!items.length) {
      col.innerHTML = `<div class="sched-col-empty">Nothing here yet.</div>`;
      return;
    }
    col.innerHTML = items.map(it => cardHtml(it, kind)).join("");
    if (kind === "upcoming") {
      col.querySelectorAll("[data-cancel]").forEach(btn => {
        btn.addEventListener("click", () => cancelItem(btn.dataset.cancel));
      });
    }
  }

  function cardHtml(item, kind) {
    const paths = item.image_paths || [];
    const n = paths.length;
    const firstUrl = paths[0] ? `/api/images/${paths[0].split("/").map(encodeURIComponent).join("/")}` : "";
    const stack = n > 1 ? `<div class="stack">+${n - 1}</div>` : "";
    const cap = escapeHtml(item.caption || "").slice(0, 200);
    const sched = fmtPHT(item.scheduled_for);
    const rel = relTime(item.scheduled_for);
    const mode = item.mode || "multi";
    const layout = item.layout;
    const modeTag = mode === "collage" && layout ? `COLLAGE/${layout}` : (n > 1 ? `${n} photos` : "1 photo");
    let pill, statusRow;
    if (kind === "upcoming") {
      pill = `<span class="sched-pill amber">APPROVED &middot; ${modeTag}</span>`;
      statusRow = `<div class="sched-qcard-meta"><span class="small muted">${escapeHtml(rel)}</span>
                   <button class="sched-btn-ghost" type="button" data-cancel="${escapeHtml(item.id)}">Cancel</button></div>`;
    } else if (kind === "posted") {
      pill = `<span class="sched-pill ok">POSTED &middot; ${modeTag}</span>`;
      const fb = item.fb_post_id ? `https://www.facebook.com/${item.fb_post_id}` : "";
      statusRow = `<div class="sched-qcard-meta">${fb ? `<a class="sched-qcard-link" href="${escapeHtml(fb)}" target="_blank" rel="noopener">View on FB &rarr;</a>` : ""}
                   <span class="small muted">${escapeHtml(relTime(item.posted_at))}</span></div>`;
    } else {
      pill = `<span class="sched-pill bad">FAILED &middot; ${modeTag}</span>`;
      const err = escapeHtml(item.error || "(no error captured)");
      statusRow = `<div class="sched-qcard-err">${err}</div>
                   <div class="sched-qcard-meta"><span class="small muted">${escapeHtml(relTime(item.posted_at))}</span></div>`;
    }
    return `<div class="sched-qcard ${kind === "failed" ? "failed" : ""}">
      <div class="sched-qcard-thumb">
        ${firstUrl ? `<img src="${escapeHtml(firstUrl)}" alt="" loading="lazy">` : ""}
        ${stack}
      </div>
      <div class="sched-qcard-body">
        <div class="sched-qcard-cap">${cap}</div>
        <div class="sched-qcard-meta">
          <span class="sched-qcard-time">${escapeHtml(sched)}</span>
          ${pill}
        </div>
        ${statusRow}
      </div>
    </div>`;
  }

  async function cancelItem(id) {
    if (!confirm("Cancel this scheduled post?")) return;
    try {
      const r = await fetch("/api/schedule/cancel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id }),
      });
      const data = await r.json();
      if (data.ok) { toast("Cancelled", "ok"); fetchQueue(); }
      else toast("Cancel failed: " + (data.error || r.status), "bad");
    } catch (e) {
      toast("Cancel error: " + e.message, "bad");
    }
  }

  // ---- composer: images strip ----
  function renderImages() {
    const strip = $("schedImageStrip");
    if (!strip) return;
    const adder = $("schedImageAdd");
    // Remove all slots (keep adder)
    Array.from(strip.querySelectorAll(".sched-image-slot")).forEach(n => n.remove());
    // Re-insert in order
    state.images.forEach((img, idx) => {
      const slot = document.createElement("div");
      slot.className = "sched-image-slot";
      slot.draggable = true;
      slot.dataset.idx = String(idx);
      slot.innerHTML = `
        <div class="order">${idx + 1}</div>
        <button class="remove" data-rm="${idx}" title="Remove" type="button">&times;</button>
        <img src="${escapeHtml(img.src_url)}" alt="">`;
      slot.addEventListener("dragstart", onDragStart);
      slot.addEventListener("dragover", onDragOver);
      slot.addEventListener("dragleave", onDragLeave);
      slot.addEventListener("drop", onDrop);
      slot.addEventListener("dragend", onDragEnd);
      strip.insertBefore(slot, adder);
    });
    strip.querySelectorAll("[data-rm]").forEach(b => {
      b.addEventListener("click", (e) => {
        e.stopPropagation();
        const i = parseInt(b.dataset.rm, 10);
        state.images.splice(i, 1);
        renderImages();
        renderPreview();
        updateLayoutTilesEnabled();
        updateImageCount();
      });
    });
    // Hide adder if at max
    if (adder) adder.style.display = state.images.length >= MAX_IMAGES ? "none" : "";
  }

  let dragIdx = null;
  function onDragStart(e) {
    dragIdx = parseInt(e.currentTarget.dataset.idx, 10);
    e.currentTarget.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
  }
  function onDragOver(e) { e.preventDefault(); e.currentTarget.classList.add("drag-over"); }
  function onDragLeave(e) { e.currentTarget.classList.remove("drag-over"); }
  function onDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove("drag-over");
    const dropIdx = parseInt(e.currentTarget.dataset.idx, 10);
    if (dragIdx === null || dragIdx === dropIdx) return;
    const [moved] = state.images.splice(dragIdx, 1);
    state.images.splice(dropIdx, 0, moved);
    dragIdx = null;
    renderImages();
    renderPreview();
  }
  function onDragEnd(e) {
    e.currentTarget.classList.remove("dragging");
    dragIdx = null;
  }

  function updateImageCount() {
    const el = $("schedImageCount");
    if (el) el.textContent = `(${state.images.length} of ${MAX_IMAGES})`;
  }

  // ---- mode + layout ----
  function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll("#schedModeToggle button").forEach(b => {
      b.classList.toggle("on", b.dataset.mode === mode);
    });
    const row = $("schedLayoutRow");
    if (row) row.classList.toggle("show", mode === "collage");
    const hint = $("schedModeHint");
    if (hint) hint.textContent = mode === "collage"
      ? "Pick a layout. Server stitches photos into one image via Pillow, then posts as a single photo to FB."
      : "FB chooses the grid based on photo count. People can swipe through photos individually.";
    updateLayoutTilesEnabled();
    renderPreview();
  }

  function setLayout(key) {
    if (!LAYOUT_NEEDS[key]) return;
    state.layout = key;
    document.querySelectorAll("#schedLayoutGrid .sched-layout-tile").forEach(t => {
      t.classList.toggle("on", t.dataset.layout === key);
    });
    renderPreview();
  }

  function updateLayoutTilesEnabled() {
    document.querySelectorAll("#schedLayoutGrid .sched-layout-tile").forEach(t => {
      const need = parseInt(t.dataset.needs, 10);
      const ok = state.images.length === need;
      t.classList.toggle("disabled", !ok);
    });
  }

  // ---- live preview ----
  function schedulePreviewUpdate() {
    if (state.previewTimer) clearTimeout(state.previewTimer);
    state.previewTimer = setTimeout(renderPreview, 150);
  }

  function renderPreview() {
    const capEl = $("schedPreviewCaption");
    const timeEl = $("schedPreviewTime");
    const gridEl = $("schedPreviewGrid");
    const collageWrap = $("schedPreviewCollageWrap");
    const collageGrid = $("schedPreviewCollage");
    if (!capEl) return;
    const cap = ($("schedCaption") || {}).value || "";
    capEl.textContent = cap || "Your caption appears here as you type...";
    const t = ($("schedTime") || {}).value || "";
    if (t) {
      const dt = new Date(`${t}:00+08:00`);
      timeEl.textContent = `Scheduled for ${dt.toLocaleString("en-PH", { month: "long", day: "numeric", hour: "numeric", minute: "2-digit", hour12: true, timeZone: "Asia/Manila" })}`;
    } else {
      timeEl.textContent = "Schedule a time to see preview";
    }

    if (state.mode === "collage" && state.images.length === LAYOUT_NEEDS[state.layout]) {
      gridEl.style.display = "none";
      gridEl.innerHTML = "";
      collageWrap.style.display = "block";
      renderCollagePreview(collageGrid, state.layout, state.images);
    } else {
      collageWrap.style.display = "none";
      gridEl.style.display = "grid";
      renderMultiPreview(gridEl, state.images);
    }
  }

  function renderMultiPreview(el, images) {
    const n = images.length;
    el.className = "fb-grid";
    if (n === 0) {
      el.innerHTML = `<div class="fb-cell"><div class="placeholder">Add an image to see preview</div></div>`;
      el.classList.add("g1");
      return;
    }
    const cls = n === 1 ? "g1" : n === 2 ? "g2" : n === 3 ? "g3" : "g4";
    el.classList.add(cls);
    const visible = images.slice(0, 4);
    el.innerHTML = visible.map((img, i) => {
      let overlay = "";
      if (n > 4 && i === 3) overlay = `<div class="more">+${n - 4}</div>`;
      return `<div class="fb-cell"><img src="${escapeHtml(img.src_url)}" alt="">${overlay}</div>`;
    }).join("");
  }

  const COLLAGE_GRIDS = {
    "2h":  { cols: "1fr 1fr", rows: "1fr", spans: [{}, {}] },
    "2v":  { cols: "1fr", rows: "1fr 1fr", spans: [{}, {}] },
    "1p2": { cols: "2fr 1fr", rows: "1fr 1fr", spans: [{ row: 2 }, {}, {}] },
    "2x2": { cols: "1fr 1fr", rows: "1fr 1fr", spans: [{}, {}, {}, {}] },
    "3h":  { cols: "1fr 1fr 1fr", rows: "1fr", spans: [{}, {}, {}] },
    "hero3": { cols: "1fr 1fr 1fr", rows: "2fr 1fr", spans: [{ col: 3 }, {}, {}, {}] },
    "ba":  { cols: "1fr 1fr", rows: "1fr", spans: [{}, {}] },
  };

  function renderCollagePreview(el, layout, images) {
    const cfg = COLLAGE_GRIDS[layout];
    if (!cfg) { el.innerHTML = ""; return; }
    el.style.gridTemplateColumns = cfg.cols;
    el.style.gridTemplateRows = cfg.rows;
    el.innerHTML = "";
    cfg.spans.forEach((sp, i) => {
      const div = document.createElement("div");
      if (sp.row) div.style.gridRow = `span ${sp.row}`;
      if (sp.col) div.style.gridColumn = `span ${sp.col}`;
      const img = images[i];
      div.innerHTML = img ? `<img src="${escapeHtml(img.src_url)}" alt="">` : `<div class="placeholder">photo ${i + 1}</div>`;
      el.appendChild(div);
    });
  }

  // ---- char count ----
  function updateCharCount() {
    const cap = ($("schedCaption") || {}).value || "";
    const el = $("schedCharCount");
    if (el) el.textContent = `${cap.length} / 2000`;
  }

  // ---- bank modal ----
  async function openBank() {
    const modal = $("schedBankModal");
    if (!modal) return;
    modal.classList.add("open");
    if (state.bankItems.length === 0) {
      try {
        const r = await fetch("/api/schedule/image-bank");
        state.bankItems = await r.json();
      } catch (e) {
        toast("Couldn't load image bank: " + e.message, "bad");
      }
    }
    renderBank();
  }

  function closeBank() {
    $("schedBankModal").classList.remove("open");
  }

  function renderBank() {
    const grid = $("schedBankGrid");
    if (!grid) return;
    const q = state.bankSearch.toLowerCase().trim();
    const filtered = state.bankItems.filter(it => {
      if (state.bankFilter !== "all" && it.type !== state.bankFilter) return false;
      if (q && !it.filename.toLowerCase().includes(q)) return false;
      return true;
    }).slice(0, 60);
    if (!filtered.length) {
      grid.innerHTML = `<div class="sched-col-empty" style="grid-column:1/-1">No images match.</div>`;
      return;
    }
    grid.innerHTML = filtered.map(it => `
      <div class="sched-bank-tile" data-path="${escapeHtml(it.path)}" data-url="${escapeHtml(it.src_url)}" data-filename="${escapeHtml(it.filename)}">
        <img src="${escapeHtml(it.src_url)}" alt="" loading="lazy">
        <div class="lbl">${escapeHtml(it.type || "")}${it.model ? " / " + escapeHtml(it.model) : ""}</div>
      </div>`).join("");
    grid.querySelectorAll(".sched-bank-tile").forEach(t => {
      t.addEventListener("click", () => {
        if (state.images.length >= MAX_IMAGES) { toast("Max 10 images", "warn"); return; }
        state.images.push({ path: t.dataset.path, src_url: t.dataset.url, filename: t.dataset.filename });
        renderImages();
        updateImageCount();
        updateLayoutTilesEnabled();
        renderPreview();
        closeBank();
      });
    });
  }

  // ---- submit ----
  async function submitForm() {
    if (state.images.length === 0) { toast("Add at least one image", "warn"); return; }
    const caption = ($("schedCaption") || {}).value.trim();
    if (!caption) { toast("Caption is empty", "warn"); return; }
    const t = ($("schedTime") || {}).value;
    if (!t) { toast("Pick a scheduled time", "warn"); return; }
    const iso = datetimeLocalToPhtIso(t);
    const payload = {
      image_paths: state.images.map(i => i.path),
      caption,
      scheduled_for: iso,
      mode: state.mode,
      layout: state.mode === "collage" ? state.layout : null,
      source: "manual",
    };
    if (state.mode === "collage") {
      const need = LAYOUT_NEEDS[state.layout];
      if (state.images.length !== need) {
        toast(`Layout ${state.layout} needs exactly ${need} images`, "warn");
        return;
      }
    }
    const btn = $("schedSubmit");
    if (btn) btn.disabled = true;
    try {
      const r = await fetch("/api/schedule/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await r.json();
      if (data.ok) {
        toast(`Scheduled: ${data.id}`, "ok");
        // Clear composer
        state.images = [];
        renderImages();
        updateImageCount();
        if ($("schedCaption")) $("schedCaption").value = "";
        updateCharCount();
        renderPreview();
        fetchQueue();
      } else {
        toast("Add failed: " + (data.error || r.status), "bad");
      }
    } catch (e) {
      toast("Network error: " + e.message, "bad");
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  // ---- activation ----
  function activate() {
    if (state.activated) { fetchQueue(); return; }
    state.activated = true;

    // Default scheduled time = next hour PHT
    const ti = $("schedTime");
    if (ti && !ti.value) ti.value = localIsoNow(60);

    // Mode toggle
    document.querySelectorAll("#schedModeToggle button").forEach(b => {
      b.addEventListener("click", () => setMode(b.dataset.mode));
    });

    // Layout tiles
    document.querySelectorAll("#schedLayoutGrid .sched-layout-tile").forEach(t => {
      t.addEventListener("click", () => {
        if (t.classList.contains("disabled")) {
          toast(`Need exactly ${t.dataset.needs} images`, "warn");
          return;
        }
        setLayout(t.dataset.layout);
      });
    });

    // Composer inputs
    const cap = $("schedCaption");
    if (cap) cap.addEventListener("input", () => { updateCharCount(); schedulePreviewUpdate(); });
    const ti2 = $("schedTime");
    if (ti2) ti2.addEventListener("input", schedulePreviewUpdate);

    // Add image
    const addBtn = $("schedImageAdd");
    if (addBtn) addBtn.addEventListener("click", openBank);

    // Submit
    const submit = $("schedSubmit");
    if (submit) submit.addEventListener("click", submitForm);

    // Bank modal
    const closeBtn = $("schedBankClose");
    if (closeBtn) closeBtn.addEventListener("click", closeBank);
    const back = $("schedBankModal");
    if (back) back.addEventListener("click", (e) => { if (e.target === back) closeBank(); });
    document.querySelectorAll(".sched-modal-toolbar .sched-chip").forEach(c => {
      c.addEventListener("click", () => {
        document.querySelectorAll(".sched-modal-toolbar .sched-chip").forEach(x => x.classList.remove("on"));
        c.classList.add("on");
        state.bankFilter = c.dataset.filter;
        renderBank();
      });
    });
    const search = $("schedBankSearch");
    if (search) search.addEventListener("input", () => { state.bankSearch = search.value; renderBank(); });

    updateImageCount();
    updateCharCount();
    updateLayoutTilesEnabled();
    renderPreview();
    fetchQueue();
    if (!state.pollTimer) state.pollTimer = setInterval(fetchQueue, POLL_MS);
  }

  document.addEventListener("tab:activated", (e) => {
    if (e.detail.tab === TAB) activate();
  });
})();
