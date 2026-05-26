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
    bankFilteredOrder: [],
    bankFilter: "all",
    bankModel: "all",
    bankSort: "newest",
    bankSearch: "",
    pollTimer: null,
    activated: false,
    previewTimer: null,
    bankPreviewItem: null,
    queueItemsById: {}, // populated from /api/schedule/queue -- lets card-click open the detail modal
    detailEditing: false, // when true, the detail modal is in edit mode
    detailItemId: null,
    colExpanded: { upcoming: false, posted: false, failed: false },
  };

  const COL_INITIAL_LIMIT = 4;

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
    // Index every item by id so card-click can look up full detail without re-fetching.
    state.queueItemsById = {};
    (data.upcoming || []).forEach(it => { it.__kind = "upcoming"; state.queueItemsById[it.id] = it; });
    (data.posted || []).forEach(it => { it.__kind = "posted"; state.queueItemsById[it.id] = it; });
    (data.failed || []).forEach(it => { it.__kind = "failed"; state.queueItemsById[it.id] = it; });
    (data.cancelled || []).forEach(it => { it.__kind = "cancelled"; state.queueItemsById[it.id] = it; });

    // Third column merges Failed + Cancelled, newest first by posted_at|added_at
    const failedAndCancelled = [...(data.failed || []), ...(data.cancelled || [])].sort((a, b) => {
      const at = b.posted_at || b.added_at || "";
      const bt = a.posted_at || a.added_at || "";
      return at.localeCompare(bt);
    });

    renderCol("schedColUpcoming", "schedCountUpcoming", data.upcoming || [], "upcoming");
    renderCol("schedColPosted", "schedCountPosted", data.posted || [], "posted");
    renderCol("schedColFailed", "schedCountFailed", failedAndCancelled, "failed");

    // If the detail modal is open on an item that just changed, refresh its content.
    if (state.detailItemId && state.queueItemsById[state.detailItemId]) {
      renderDetailBody(state.queueItemsById[state.detailItemId], state.detailEditing);
    }
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

    const expanded = state.colExpanded[kind];
    const overflow = items.length - COL_INITIAL_LIMIT;
    const visible = expanded ? items : items.slice(0, COL_INITIAL_LIMIT);

    let html = visible.map(it => cardHtml(it, kind)).join("");
    if (overflow > 0) {
      const label = expanded
        ? `Show less &uarr;`
        : `Show ${overflow} more &darr;`;
      html += `<button type="button" class="sched-col-toggle" data-col-kind="${kind}">${label}</button>`;
    }
    col.innerHTML = html;

    // Whole card opens the detail modal. Cancel button (inside the card) stops
    // propagation so it doesn't open the modal too.
    col.querySelectorAll(".sched-qcard").forEach(card => {
      card.addEventListener("click", () => openDetail(card.dataset.id));
    });
    if (kind === "upcoming") {
      col.querySelectorAll("[data-cancel]").forEach(btn => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          cancelItem(btn.dataset.cancel);
        });
      });
      col.querySelectorAll("[data-verify-meta]").forEach(btn => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          verifyOnMeta(btn.dataset.verifyMeta, btn);
        });
      });
    }
    const toggleBtn = col.querySelector(".sched-col-toggle");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        state.colExpanded[kind] = !state.colExpanded[kind];
        renderCol(colId, countId, items, kind);
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
      if (item.status === "SCHEDULED_AT_META") {
        pill = `<span class="sched-pill blue" title="Handed off to Facebook — will fire even if your laptop is off">ON META &middot; ${modeTag}</span>`;
      } else {
        pill = `<span class="sched-pill amber" title="Sitting in local queue — fires via hourly cron">APPROVED &middot; ${modeTag}</span>`;
      }
      const verifyBtn = item.status === "SCHEDULED_AT_META"
        ? `<button class="sched-btn-ghost" type="button" data-verify-meta="${escapeHtml(item.id)}" title="Ping Meta Graph API to confirm the post is still scheduled">Verify</button>`
        : "";
      const viewBtn = (item.status === "SCHEDULED_AT_META" && item.fb_view_url)
        ? `<a class="sched-btn-ghost sched-view-link" href="${escapeHtml(item.fb_view_url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()" title="Open this scheduled post on Facebook (admin preview)">View on FB</a>`
        : "";
      statusRow = `<div class="sched-qcard-meta"><span class="small muted">${escapeHtml(rel)}</span>
                   <span class="sched-qcard-actions">${viewBtn}${verifyBtn}<button class="sched-btn-ghost" type="button" data-cancel="${escapeHtml(item.id)}">Cancel</button></span></div>`;
    } else if (kind === "posted") {
      pill = `<span class="sched-pill ok">POSTED &middot; ${modeTag}</span>`;
      const fb = item.fb_post_id ? `https://www.facebook.com/${item.fb_post_id}` : "";
      statusRow = `<div class="sched-qcard-meta">${fb ? `<a class="sched-qcard-link" href="${escapeHtml(fb)}" target="_blank" rel="noopener">View on FB &rarr;</a>` : ""}
                   <span class="small muted">${escapeHtml(relTime(item.posted_at))}</span></div>`;
    } else if (item.__kind === "cancelled") {
      pill = `<span class="sched-pill grey">CANCELLED &middot; ${modeTag}</span>`;
      statusRow = `<div class="sched-qcard-meta"><span class="small muted">${escapeHtml(relTime(item.posted_at || item.added_at))}</span></div>`;
    } else {
      pill = `<span class="sched-pill bad">FAILED &middot; ${modeTag}</span>`;
      const err = escapeHtml(item.error || "(no error captured)");
      statusRow = `<div class="sched-qcard-err">${err}</div>
                   <div class="sched-qcard-meta"><span class="small muted">${escapeHtml(relTime(item.posted_at))}</span></div>`;
    }
    return `<div class="sched-qcard ${item.__kind === "failed" ? "failed" : (item.__kind === "cancelled" ? "cancelled" : "")}" data-id="${escapeHtml(item.id)}" title="Click for details">
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

  // -- Queue item detail modal -------------------------------------------------

  function isoToLocalInputValue(iso) {
    // Convert "2026-05-25T06:30:00+08:00" -> "2026-05-25T06:30" for <input type="datetime-local">
    if (!iso) return "";
    const m = String(iso).match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})/);
    return m ? `${m[1]}T${m[2]}` : "";
  }

  function localInputToPhtIso(value) {
    // "2026-05-25T06:30" interpreted as PHT
    if (!value) return "";
    return `${value}:00+08:00`;
  }

  function renderDetailBody(item, editing) {
    const body = $("schedQueueDetailBody");
    const foot = $("schedQueueDetailFoot");
    const title = $("schedQueueDetailTitle");
    if (!body || !foot || !item) return;

    const kind = item.__kind || "upcoming";
    title.textContent = kind === "upcoming" ? "Upcoming post" : (kind === "posted" ? "Posted" : (kind === "cancelled" ? "Cancelled post" : "Failed post"));

    const paths = item.image_paths || [];
    // Use the cached 480px JPEG thumbs instead of the full 1-2MB PNGs. The FB
    // card caps at 560px so 480 is plenty; cells in g4 layout are ~280px so we
    // even have headroom for retina. Cuts modal open from ~6MB to ~80KB.
    const images = paths.map(p => {
      const encoded = p.split("/").map(encodeURIComponent).join("/");
      return { path: p, src_url: `/api/thumb/${encoded}?w=480` };
    });
    const mode = item.mode || "multi";
    const layout = item.layout;
    const modeTag = mode === "collage" && layout ? `COLLAGE / ${layout}` : (paths.length > 1 ? `${paths.length} photos` : "1 photo");
    const sched = fmtPHT(item.scheduled_for);
    const rel = relTime(item.scheduled_for);

    // Time label inside the FB card (matches "Scheduled for Mmm DD at H:MM AM/PM" style of the live preview)
    let timeLabel;
    if (item.scheduled_for) {
      const dt = new Date(item.scheduled_for);
      timeLabel = `Scheduled for ${dt.toLocaleString("en-PH", { month: "long", day: "numeric", hour: "numeric", minute: "2-digit", hour12: true, timeZone: "Asia/Manila" })}`;
    } else if (item.posted_at) {
      const dt = new Date(item.posted_at);
      timeLabel = `${kind === "posted" ? "Posted" : "Updated"} ${dt.toLocaleString("en-PH", { month: "long", day: "numeric", hour: "numeric", minute: "2-digit", hour12: true, timeZone: "Asia/Manila" })}`;
    } else {
      timeLabel = "";
    }

    // Build caption + time blocks (editable in edit mode for upcoming)
    let captionBlock, timeBlock;
    if (editing && kind === "upcoming") {
      captionBlock = `<textarea id="schedQDCaption" class="sched-qd-cap-edit">${escapeHtml(item.caption || "")}</textarea>`;
      timeBlock = `<input type="datetime-local" id="schedQDTime" class="sched-qd-time-edit" value="${escapeHtml(isoToLocalInputValue(item.scheduled_for))}">`;
    } else {
      captionBlock = `<div class="fb-caption">${escapeHtml(item.caption || "(no caption)")}</div>`;
      timeBlock = `<div class="fb-time">${escapeHtml(timeLabel)}</div>`;
    }

    // Images block: collage if mode=collage with matching image count, else grid
    const collageCfg = (mode === "collage" && layout && paths.length === (LAYOUT_NEEDS[layout] || -1)) ? COLLAGE_GRIDS[layout] : null;
    const imagesHtml = collageCfg
      ? `<div class="fb-collage-wrap"><div class="fb-collage-grid" id="schedQDCollage"></div></div>`
      : `<div class="fb-grid" id="schedQDGrid"></div>`;

    // Admin strip below the FB card -- status pill + relative time + extras
    const statusPill = kind === "upcoming"
      ? `<span class="sched-pill amber">APPROVED &middot; ${modeTag}</span>`
      : kind === "posted"
      ? `<span class="sched-pill ok">POSTED &middot; ${modeTag}</span>`
      : `<span class="sched-pill bad">FAILED &middot; ${modeTag}</span>`;

    let adminExtra = "";
    if (kind === "posted" && item.fb_post_id) {
      const fb = `https://www.facebook.com/${item.fb_post_id}`;
      adminExtra = `<a class="sched-qcard-link" href="${escapeHtml(fb)}" target="_blank" rel="noopener" style="margin-left:auto">View on FB &rarr;</a>`;
    } else if (kind === "failed" && item.error) {
      adminExtra = `<div class="sched-qd-err" style="margin-top:8px">${escapeHtml(item.error)}</div>`;
    }

    body.innerHTML = `
      <div class="fb-card">
        <div class="fb-head">
          <div class="fb-avatar">D</div>
          <div class="fb-meta">
            <div class="fb-name">DuberyMNL</div>
            ${timeBlock}
          </div>
        </div>
        ${captionBlock}
        ${imagesHtml}
        <div class="fb-actions">
          <div>&#128077; Like</div>
          <div>&#128172; Comment</div>
          <div>&#8631; Share</div>
        </div>
      </div>
      <div class="sched-qd-admin" style="display:flex; gap:8px; align-items:center; flex-wrap:wrap; padding:4px 2px; font-size:11px; color:var(--muted)">
        ${statusPill}
        <span>${escapeHtml(rel)}</span>
        ${adminExtra && !adminExtra.startsWith("<div") ? adminExtra : ""}
      </div>
      ${adminExtra && adminExtra.startsWith("<div") ? adminExtra : ""}
    `;

    // Populate the image block AFTER the markup is in the DOM (renderMulti/Collage write into elements)
    if (collageCfg) {
      const el = $("schedQDCollage");
      if (el) renderCollagePreview(el, layout, images);
    } else {
      const el = $("schedQDGrid");
      if (el) renderMultiPreview(el, images);
    }

    // Footer actions
    if (kind === "upcoming") {
      if (editing) {
        foot.innerHTML = `
          <button type="button" class="sched-btn-ghost" id="schedQDCancelEdit">Cancel edit</button>
          <button type="button" class="sched-btn-accent" id="schedQDSave">Save changes</button>
        `;
        foot.querySelector("#schedQDCancelEdit").addEventListener("click", () => { state.detailEditing = false; renderDetailBody(item, false); });
        foot.querySelector("#schedQDSave").addEventListener("click", () => saveDetailEdit(item.id));
      } else {
        foot.innerHTML = `
          <button type="button" class="sched-btn-ghost" id="schedQDCancelPost" style="color:var(--bad)">Cancel post</button>
          <button type="button" class="sched-btn-accent" id="schedQDEditBtn">Edit</button>
          <button type="button" class="sched-btn-ghost" id="schedQDClose">Close</button>
        `;
        foot.querySelector("#schedQDEditBtn").addEventListener("click", () => { state.detailEditing = true; renderDetailBody(item, true); });
        foot.querySelector("#schedQDCancelPost").addEventListener("click", async () => {
          await cancelItem(item.id);
          closeDetail();
        });
        foot.querySelector("#schedQDClose").addEventListener("click", closeDetail);
      }
    } else {
      foot.innerHTML = `<button type="button" class="sched-btn-ghost" id="schedQDClose">Close</button>`;
      foot.querySelector("#schedQDClose").addEventListener("click", closeDetail);
    }
  }

  function openDetail(itemId) {
    const item = state.queueItemsById[itemId];
    if (!item) return;
    state.detailItemId = itemId;
    state.detailEditing = false;
    renderDetailBody(item, false);
    const overlay = $("schedQueueDetail");
    if (overlay) overlay.classList.add("open");
  }

  function closeDetail() {
    state.detailItemId = null;
    state.detailEditing = false;
    const overlay = $("schedQueueDetail");
    if (overlay) overlay.classList.remove("open");
  }

  async function saveDetailEdit(itemId) {
    const capEl = $("schedQDCaption");
    const timeEl = $("schedQDTime");
    if (!capEl || !timeEl) return;
    const newCaption = capEl.value;
    const newTimeIso = localInputToPhtIso(timeEl.value);
    if (!newTimeIso) { toast("Time required", "bad"); return; }
    if (new Date(newTimeIso).getTime() <= Date.now()) {
      toast("Scheduled time must be in the future", "bad");
      return;
    }
    try {
      const r = await fetch("/api/schedule/edit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: itemId, caption: newCaption, scheduled_for: newTimeIso }),
      });
      const data = await r.json();
      if (!data.ok) { toast("Save failed: " + (data.error || r.status), "bad"); return; }
      toast("Saved", "ok");
      state.detailEditing = false;
      await fetchQueue(); // re-renders + updates the open modal via renderQueue
    } catch (e) {
      toast("Save error: " + e.message, "bad");
    }
  }

  async function verifyOnMeta(id, btn) {
    if (!id) return;
    const originalText = btn ? btn.textContent : "";
    if (btn) { btn.disabled = true; btn.textContent = "Checking..."; }
    try {
      const r = await fetch("/api/schedule/verify-meta", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id }),
      });
      const data = await r.json();
      if (!data.ok) {
        toast("Verify error: " + (data.error || r.status), "bad");
        if (btn) { btn.textContent = "Verify"; btn.disabled = false; }
        return;
      }
      if (data.state === "scheduled") {
        const when = data.scheduled_publish_time
          ? new Date(data.scheduled_publish_time * 1000).toLocaleString("en-PH", { timeZone: "Asia/Manila", dateStyle: "medium", timeStyle: "short" })
          : "unknown time";
        toast(`On Meta -- fires ${when}`, "ok");
        if (btn) { btn.textContent = "Verified ✓"; btn.classList.add("verified"); }
        setTimeout(() => { if (btn) { btn.textContent = "Verify"; btn.classList.remove("verified"); btn.disabled = false; } }, 4000);
      } else if (data.state === "published") {
        toast("Post already fired on Meta -- worker will sync queue to POSTED on next tick", "warn");
        if (btn) { btn.textContent = "Fired"; btn.disabled = false; }
        fetchQueue();
      } else if (data.state === "missing") {
        toast("Drift: Meta does not have this scheduled post. Detail: " + (data.detail || ""), "bad");
        if (btn) { btn.textContent = "Missing ✗"; btn.classList.add("drift"); btn.disabled = false; }
      } else {
        toast("Unexpected state: " + data.state, "bad");
        if (btn) { btn.textContent = "Verify"; btn.disabled = false; }
      }
    } catch (e) {
      toast("Verify error: " + e.message, "bad");
      if (btn) { btn.textContent = originalText || "Verify"; btn.disabled = false; }
    }
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
        if (window.__schedNotifyImages) window.__schedNotifyImages();
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
    if (window.__schedNotifyImages) window.__schedNotifyImages();
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
  async function refreshBank() {
    try {
      const includeArchived = state.bankFilter === "archived" ? "?include_archived=1" : "";
      const r = await fetch("/api/schedule/image-bank" + includeArchived);
      state.bankItems = await r.json();
    } catch (e) {
      toast("Couldn't load image bank: " + e.message, "bad");
    }
  }

  async function openBank() {
    const modal = $("schedBankModal");
    if (!modal) return;
    modal.classList.add("open");
    if (state.bankItems.length === 0) {
      await refreshBank();
    }
    populateModelDropdown();
    renderBank();
  }

  function populateModelDropdown() {
    const sel = $("schedBankModel");
    if (!sel) return;
    const models = new Set();
    state.bankItems.forEach(it => { if (it.model) models.add(it.model); });
    const sorted = Array.from(models).sort();
    // Preserve current selection if still valid
    const currentVal = sel.value || state.bankModel;
    sel.innerHTML = `<option value="all">All models (${state.bankItems.length})</option>` +
      sorted.map(m => {
        const n = state.bankItems.filter(it => it.model === m).length;
        return `<option value="${escapeHtml(m)}">${escapeHtml(m)} (${n})</option>`;
      }).join("");
    sel.value = sorted.includes(currentVal) ? currentVal : "all";
    state.bankModel = sel.value;
  }

  function closeBank() {
    $("schedBankModal").classList.remove("open");
  }

  function renderBank() {
    const grid = $("schedBankGrid");
    if (!grid) return;
    const q = state.bankSearch.toLowerCase().trim();
    let filtered = state.bankItems.filter(it => {
      if (state.bankFilter === "favorites") {
        if (!it.favorite) return false;
      } else if (state.bankFilter === "archived") {
        if (!it.archived) return false;
      } else if (state.bankFilter === "new") {
        if (it.source !== "new") return false;
      } else if (state.bankFilter !== "all" && it.type !== state.bankFilter) {
        return false;
      }
      if (state.bankModel && state.bankModel !== "all" && it.model !== state.bankModel) return false;
      if (q && !it.filename.toLowerCase().includes(q)) return false;
      return true;
    });
    // Sort
    if (state.bankSort === "oldest") {
      filtered.sort((a, b) => (a.tagged_at || "").localeCompare(b.tagged_at || "") || a.filename.localeCompare(b.filename));
    } else if (state.bankSort === "model") {
      filtered.sort((a, b) => (a.model || "~").localeCompare(b.model || "~") || (b.tagged_at || "").localeCompare(a.tagged_at || ""));
    } else { // newest (default)
      filtered.sort((a, b) => (b.tagged_at || "").localeCompare(a.tagged_at || "") || b.filename.localeCompare(a.filename));
    }
    // Update result count chip
    const countEl = $("schedBankCount");
    if (countEl) countEl.textContent = `${filtered.length} image${filtered.length === 1 ? "" : "s"}`;
    // Snapshot the displayed order so the preview lightbox can navigate it
    state.bankFilteredOrder = filtered.slice();
    if (!filtered.length) {
      grid.innerHTML = `<div class="sched-col-empty" style="grid-column:1/-1">No images match.</div>`;
      return;
    }
    const selectedPaths = new Set(state.images.map(i => i.path));
    grid.innerHTML = filtered.map(it => {
      const isSel = selectedPaths.has(it.path);
      const isFav = !!it.favorite;
      const isDraft = it.source === "new";
      const isArchived = !!it.archived;
      const typeLabel = isDraft ? "DRAFT" : (it.type || "").toString();
      const tagClass = isDraft ? "sched-bank-draft" : "sched-bank-tag";
      const thumb = it.thumb_url || it.src_url;
      const star = isFav ? "★" : "☆";
      const classes = ["sched-bank-tile"];
      if (isSel) classes.push("selected");
      if (isArchived) classes.push("archived");
      return `
      <div class="${classes.join(' ')}" data-path="${escapeHtml(it.path)}" data-url="${escapeHtml(it.src_url)}" data-filename="${escapeHtml(it.filename)}" data-type="${escapeHtml(it.type || '')}" data-model="${escapeHtml(it.model || '')}" data-favorite="${isFav ? '1' : '0'}" data-archived="${isArchived ? '1' : '0'}" data-source="${escapeHtml(it.source || '')}">
        ${typeLabel ? `<div class="${tagClass}">${escapeHtml(typeLabel)}</div>` : ''}
        <button type="button" class="sched-bank-fav ${isFav ? 'on' : ''}" data-fav-path="${escapeHtml(it.path)}" title="${isFav ? 'Remove favorite' : 'Mark as favorite'}">${star}</button>
        <img src="${escapeHtml(thumb)}" alt="" loading="lazy" decoding="async">
        <div class="lbl">${escapeHtml(it.filename || '')}</div>
      </div>`;
    }).join("");
    grid.querySelectorAll(".sched-bank-fav").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleFavorite(btn.dataset.favPath);
      });
    });
    grid.querySelectorAll(".sched-bank-tile").forEach(t => {
      t.addEventListener("click", () => openBankPreview({
        path: t.dataset.path,
        src_url: t.dataset.url,
        filename: t.dataset.filename,
        type: t.dataset.type,
        model: t.dataset.model,
        favorite: t.dataset.favorite === "1",
        archived: t.dataset.archived === "1",
        source: t.dataset.source,
      }));
    });
  }

  async function toggleFavorite(path) {
    if (!path) return;
    try {
      const r = await fetch("/api/schedule/favorites", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path, action: "toggle" }),
      });
      const data = await r.json();
      if (!data.ok) { toast(data.error || "Favorite failed", "bad"); return; }
      // Mutate cached bankItems so we don't refetch the whole bank
      const idx = state.bankItems.findIndex(i => i.path === path);
      if (idx >= 0) state.bankItems[idx].favorite = !!data.favorited;
      // If the lightbox is open on this item, sync the button state
      if (state.bankPreviewItem && state.bankPreviewItem.path === path) {
        state.bankPreviewItem.favorite = !!data.favorited;
        updatePreviewFavBtn();
      }
      renderBank();
    } catch (e) {
      toast("Favorite error: " + e.message, "bad");
    }
  }

  function updatePreviewFavBtn() {
    const btn = $("schedBankPreviewFav");
    if (!btn || !state.bankPreviewItem) return;
    const on = !!state.bankPreviewItem.favorite;
    btn.classList.toggle("on", on);
    btn.innerHTML = (on ? "★" : "☆") + " " + (on ? "Favorited" : "Favorite");
    btn.title = on ? "Remove favorite" : "Mark as favorite";
  }

  // ---- bank preview lightbox ----
  function openBankPreview(item) {
    const overlay = $("schedBankPreview");
    if (!overlay) return;
    state.bankPreviewItem = item;
    const img = $("schedBankPreviewImg");
    if (img) img.src = item.src_url;
    const name = $("schedBankPreviewName");
    if (name) name.textContent = item.filename || "";
    const meta = $("schedBankPreviewMeta");
    if (meta) {
      const parts = [];
      if (item.type) parts.push(item.type);
      if (item.model) parts.push(item.model);
      const order = state.bankFilteredOrder || [];
      const idx = order.findIndex(i => i.path === item.path);
      if (idx >= 0 && order.length > 1) parts.push(`${idx + 1} / ${order.length}`);
      meta.textContent = parts.join(" - ");
    }
    updatePreviewNavBtns();
    const btn = $("schedBankPreviewSelect");
    const already = state.images.some(i => i.path === item.path);
    if (btn) {
      if (already) {
        btn.textContent = "Already added";
        btn.classList.add("selected");
        btn.disabled = true;
      } else if (state.images.length >= MAX_IMAGES) {
        btn.textContent = "Post is full (10 max)";
        btn.classList.remove("selected");
        btn.disabled = true;
      } else {
        btn.textContent = "Add to post";
        btn.classList.remove("selected");
        btn.disabled = false;
      }
    }
    updatePreviewFavBtn();
    updatePreviewArchiveBtn();
    overlay.classList.add("open");
  }

  function updatePreviewArchiveBtn() {
    const btn = $("schedBankPreviewArchive");
    if (!btn || !state.bankPreviewItem) return;
    const on = !!state.bankPreviewItem.archived;
    btn.classList.toggle("on", on);
    btn.textContent = on ? "Unarchive" : "Archive";
  }

  function updatePreviewNavBtns() {
    const prev = document.getElementById("schedBankPreviewPrev");
    const next = document.getElementById("schedBankPreviewNext");
    const order = state.bankFilteredOrder || [];
    if (!state.bankPreviewItem || order.length <= 1) {
      if (prev) prev.style.display = "none";
      if (next) next.style.display = "none";
      return;
    }
    const idx = order.findIndex(i => i.path === state.bankPreviewItem.path);
    if (prev) {
      prev.style.display = "flex";
      prev.disabled = idx <= 0;
    }
    if (next) {
      next.style.display = "flex";
      next.disabled = idx < 0 || idx >= order.length - 1;
    }
  }

  function navPreview(direction) {
    if (!state.bankPreviewItem) return;
    const order = state.bankFilteredOrder || [];
    if (order.length <= 1) return;
    const idx = order.findIndex(i => i.path === state.bankPreviewItem.path);
    if (idx < 0) return;
    const target = idx + (direction === "next" ? 1 : -1);
    if (target < 0 || target >= order.length) return;
    openBankPreview(order[target]);
  }

  function viewPreviewFull() {
    const img = document.getElementById("schedBankPreviewImg");
    if (!img) return;
    try {
      const req = img.requestFullscreen || img.webkitRequestFullscreen || img.msRequestFullscreen;
      if (req) {
        req.call(img).catch((e) => toast("Fullscreen blocked: " + e.message, "bad"));
      } else {
        toast("Fullscreen API not supported in this browser", "bad");
      }
    } catch (e) {
      toast("Fullscreen error: " + e.message, "bad");
    }
  }

  async function copyPreviewPath() {
    if (!state.bankPreviewItem) return;
    const path = state.bankPreviewItem.path || "";
    if (!path) { toast("No path to copy", "bad"); return; }
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(path);
      } else {
        const ta = document.createElement("textarea");
        ta.value = path;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }
      toast("Copied: " + path, "ok");
    } catch (e) {
      toast("Copy failed: " + e.message, "bad");
    }
  }

  async function toggleArchivePreview() {
    if (!state.bankPreviewItem) return;
    const path = state.bankPreviewItem.path;
    try {
      const r = await fetch("/api/schedule/image-bank/archive", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path, action: "toggle" }),
      });
      const data = await r.json();
      if (!data.ok) { toast(data.error || "Archive failed", "bad"); return; }
      const idx = state.bankItems.findIndex(i => i.path === path);
      if (idx >= 0) state.bankItems[idx].archived = !!data.archived;
      state.bankPreviewItem.archived = !!data.archived;
      updatePreviewArchiveBtn();
      // If the user just archived an item while viewing the default bank, drop it from view
      if (data.archived && state.bankFilter !== "archived") {
        closeBankPreview();
      }
      renderBank();
      toast(data.archived ? "Archived" : "Unarchived", "ok");
    } catch (e) {
      toast("Archive error: " + e.message, "bad");
    }
  }

  async function deletePreview() {
    if (!state.bankPreviewItem) return;
    const item = state.bankPreviewItem;
    if (!confirm(`Delete "${item.filename}"?\nThe file moves to .tmp/bank_trash/ and can be restored manually.`)) return;
    try {
      const r = await fetch("/api/schedule/image-bank/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: item.path }),
      });
      const data = await r.json();
      if (!data.ok) { toast(data.error || "Delete failed", "bad"); return; }
      // Drop from local cache, drop from any current composer
      state.bankItems = state.bankItems.filter(i => i.path !== item.path);
      state.images = state.images.filter(i => i.path !== item.path);
      renderImages();
      updateImageCount();
      renderPreview();
      closeBankPreview();
      renderBank();
      toast(`Deleted (moved to ${data.moved_to})`, "ok");
    } catch (e) {
      toast("Delete error: " + e.message, "bad");
    }
  }

  function closeBankPreview() {
    const overlay = $("schedBankPreview");
    if (overlay) overlay.classList.remove("open");
    state.bankPreviewItem = null;
  }

  function selectBankPreview() {
    const item = state.bankPreviewItem;
    if (!item) return;
    if (state.images.length >= MAX_IMAGES) { toast("Max 10 images", "warn"); return; }
    if (state.images.some(i => i.path === item.path)) { toast("Already added", "warn"); return; }
    state.images.push({ path: item.path, src_url: item.src_url, filename: item.filename });
    renderImages();
    updateImageCount();
    updateLayoutTilesEnabled();
    renderPreview();
    renderBank();      // refresh selected-state highlighting
    closeBankPreview();
    closeBank();
    if (window.__schedNotifyImages) window.__schedNotifyImages();
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
        if (data.handed_off) {
          toast(`Scheduled on Meta: ${data.id}`, "ok");
        } else {
          toast(`Queued locally: ${data.id} (will hand off or fire on next cron)`, "warn");
        }
        // Clear composer
        state.images = [];
        renderImages();
        updateImageCount();
        if ($("schedCaption")) $("schedCaption").value = "";
        updateCharCount();
        renderPreview();
        fetchQueue();
        if (window.__schedNotifyImages) window.__schedNotifyImages();
      } else {
        toast("Add failed: " + (data.error || r.status), "bad");
      }
    } catch (e) {
      toast("Network error: " + e.message, "bad");
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  // ---- top-level sub-tabs (Compose / AI Suggest / Calendar) ----
  const SUBTAB_KEY = "cc.schedule.tab";
  const VALID_SUBTABS = ["compose", "suggest", "calendar"];

  function setScheduleTab(tab) {
    if (!VALID_SUBTABS.includes(tab)) tab = "compose";
    document.querySelectorAll("#schedToptabBar .sched-toptab").forEach(b => {
      b.classList.toggle("on", b.dataset.schedTab === tab);
    });
    const panels = { compose: "composerPanel", suggest: "suggestPanel", calendar: "calendarPanel" };
    Object.entries(panels).forEach(([key, id]) => {
      const el = document.getElementById(id);
      if (el) el.style.display = (key === tab) ? "" : "none";
    });
    try { localStorage.setItem(SUBTAB_KEY, tab); } catch (e) { /* ignore */ }

    // Lazy-load hooks (Phase 2/3 modules attach here)
    if (tab === "suggest" && window.__schedChat && typeof window.__schedChat.activate === "function") {
      try { window.__schedChat.activate(); } catch (e) { console.error("schedChat.activate failed", e); }
    }
    if (tab === "calendar" && window.__schedCalendar && typeof window.__schedCalendar.activate === "function") {
      try { window.__schedCalendar.activate(); } catch (e) { console.error("schedCalendar.activate failed", e); }
    }
  }
  // Expose for other modules + future debugging
  window.__schedTab = { set: setScheduleTab, getCurrent: () => {
    try { return localStorage.getItem(SUBTAB_KEY) || "compose"; } catch (e) { return "compose"; }
  } };

  function wireSubTabs() {
    document.querySelectorAll("#schedToptabBar .sched-toptab").forEach(b => {
      b.addEventListener("click", () => setScheduleTab(b.dataset.schedTab));
    });
    // Restore last-active
    let last = "compose";
    try { last = localStorage.getItem(SUBTAB_KEY) || "compose"; } catch (e) { /* ignore */ }
    setScheduleTab(last);
  }

  // ---- custom datetime picker ----
  const PEAK_TIMES = [
    { h: 6,  m: 0,  label: "6:00 AM" },
    { h: 8,  m: 0,  label: "8:00 AM" },
    { h: 10, m: 0,  label: "10:00 AM" },
    { h: 12, m: 0,  label: "12:00 PM" },
    { h: 15, m: 0,  label: "3:00 PM" },
    { h: 17, m: 0,  label: "5:00 PM" },
    { h: 18, m: 0,  label: "6:00 PM" },
    { h: 19, m: 0,  label: "7:00 PM" },
    { h: 21, m: 0,  label: "9:00 PM" },
    { h: 22, m: 0,  label: "10:00 PM" },
  ];
  const dtPicker = {
    viewY: null,
    viewM: null, // 0-11
    sel: null,   // {y, m, d, h, min} or null
    bind() {
      const trig = $("schedDtTrigger");
      const panel = $("schedDtPanel");
      if (!trig || !panel) return;
      const hidden = $("schedTime");
      // Seed sel from current hidden value, or default to "next hour"
      if (hidden && hidden.value) {
        const v = this.parseLocal(hidden.value);
        if (v) this.sel = v;
      }
      if (!this.sel) {
        const d = new Date(Date.now() + 60 * 60 * 1000);
        const phtIsoStr = d.toLocaleString("en-US", { timeZone: "Asia/Manila", hour12: false, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
        // Format from toLocaleString varies; safer to use Date directly assuming local matches PHT-ish
        this.sel = { y: d.getFullYear(), m: d.getMonth(), d: d.getDate(), h: d.getHours(), min: (Math.ceil(d.getMinutes()/15)*15) % 60 };
        if (this.sel.min === 0 && d.getMinutes() > 0) this.sel.h = (this.sel.h + 1) % 24;
        this.commit();
      }
      this.viewY = this.sel.y;
      this.viewM = this.sel.m;
      trig.addEventListener("click", () => this.toggle());
      $("schedDtPrev").addEventListener("click", () => { this.viewM--; if (this.viewM < 0) { this.viewM = 11; this.viewY--; } this.renderCal(); });
      $("schedDtNext").addEventListener("click", () => { this.viewM++; if (this.viewM > 11) { this.viewM = 0; this.viewY++; } this.renderCal(); });
      $("schedDtToday").addEventListener("click", () => {
        const t = new Date();
        this.viewY = t.getFullYear(); this.viewM = t.getMonth();
        this.renderCal();
      });
      $("schedDtClear").addEventListener("click", () => { this.sel = null; this.commit(); this.renderAll(); });
      $("schedDtDone").addEventListener("click", () => this.close());
      panel.querySelectorAll("[data-step]").forEach(b => {
        b.addEventListener("click", () => this.step(b.dataset.step, parseInt(b.dataset.dir, 10)));
      });
      panel.querySelectorAll("[data-ampm]").forEach(b => {
        b.addEventListener("click", () => this.setAmPm(b.dataset.ampm));
      });
      // Outside click + escape
      document.addEventListener("click", (e) => {
        if (!panel || panel.hidden) return;
        if (e.target.closest("#schedDt")) return;
        this.close();
      });
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && panel && !panel.hidden) this.close();
      });
      this.renderAll();
    },
    parseLocal(v) {
      // "YYYY-MM-DDTHH:MM"
      const m = String(v).match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
      if (!m) return null;
      return { y: +m[1], m: +m[2] - 1, d: +m[3], h: +m[4], min: +m[5] };
    },
    toLocal() {
      if (!this.sel) return "";
      const pad = n => String(n).padStart(2, "0");
      const s = this.sel;
      return `${s.y}-${pad(s.m + 1)}-${pad(s.d)}T${pad(s.h)}:${pad(s.min)}`;
    },
    commit() {
      const hidden = $("schedTime");
      if (!hidden) return;
      hidden.value = this.toLocal();
      hidden.dispatchEvent(new Event("input", { bubbles: true }));
    },
    open() {
      $("schedDtPanel").hidden = false;
      $("schedDtTrigger").setAttribute("aria-expanded", "true");
      this.renderAll();
    },
    close() {
      const p = $("schedDtPanel");
      if (p) p.hidden = true;
      $("schedDtTrigger").setAttribute("aria-expanded", "false");
    },
    toggle() { ($("schedDtPanel").hidden) ? this.open() : this.close(); },
    renderAll() {
      this.renderTrigger();
      this.renderCal();
      this.renderChips();
      this.renderSteppers();
    },
    renderTrigger() {
      const disp = $("schedDtDisplay");
      if (!disp) return;
      if (!this.sel) {
        disp.textContent = "Pick a time";
        disp.classList.add("placeholder");
        return;
      }
      const d = new Date(this.sel.y, this.sel.m, this.sel.d, this.sel.h, this.sel.min);
      const datePart = d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
      const timePart = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
      disp.textContent = `${datePart}  ·  ${timePart}`;
      disp.classList.remove("placeholder");
    },
    renderCal() {
      const grid = $("schedDtGrid");
      const label = $("schedDtMonthLabel");
      if (!grid || !label) return;
      const months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
      label.textContent = `${months[this.viewM]} ${this.viewY}`;
      const first = new Date(this.viewY, this.viewM, 1);
      const startDow = first.getDay(); // 0 Sun
      const daysIn = new Date(this.viewY, this.viewM + 1, 0).getDate();
      const prevDays = new Date(this.viewY, this.viewM, 0).getDate();
      const today = new Date();
      const todayY = today.getFullYear(), todayM = today.getMonth(), todayD = today.getDate();
      let cells = "";
      // leading muted days from prev month
      for (let i = startDow - 1; i >= 0; i--) {
        const d = prevDays - i;
        cells += `<button type="button" class="sched-dt-day muted past" disabled>${d}</button>`;
      }
      for (let d = 1; d <= daysIn; d++) {
        const isPast = (this.viewY < todayY) ||
          (this.viewY === todayY && this.viewM < todayM) ||
          (this.viewY === todayY && this.viewM === todayM && d < todayD);
        const isToday = (this.viewY === todayY && this.viewM === todayM && d === todayD);
        const isSel = this.sel && this.sel.y === this.viewY && this.sel.m === this.viewM && this.sel.d === d;
        const cls = ["sched-dt-day"];
        if (isPast) cls.push("past");
        if (isToday) cls.push("today");
        if (isSel) cls.push("selected");
        const dis = isPast ? "disabled" : "";
        cells += `<button type="button" class="${cls.join(" ")}" data-day="${d}" ${dis}>${d}</button>`;
      }
      // trailing muted to fill 6-row grid
      const total = startDow + daysIn;
      const trailing = (7 - (total % 7)) % 7;
      for (let i = 1; i <= trailing; i++) {
        cells += `<button type="button" class="sched-dt-day muted past" disabled>${i}</button>`;
      }
      grid.innerHTML = cells;
      grid.querySelectorAll("[data-day]").forEach(b => {
        b.addEventListener("click", () => {
          if (!this.sel) this.sel = { y: this.viewY, m: this.viewM, d: parseInt(b.dataset.day,10), h: 18, min: 0 };
          else { this.sel.y = this.viewY; this.sel.m = this.viewM; this.sel.d = parseInt(b.dataset.day,10); }
          this.commit(); this.renderAll();
        });
      });
    },
    renderChips() {
      const wrap = $("schedDtChips");
      if (!wrap) return;
      wrap.innerHTML = PEAK_TIMES.map(t => {
        const isSel = this.sel && this.sel.h === t.h && this.sel.min === t.m;
        return `<button type="button" class="sched-dt-chip ${isSel ? 'selected' : ''}" data-h="${t.h}" data-m="${t.m}">${t.label}</button>`;
      }).join("");
      wrap.querySelectorAll(".sched-dt-chip").forEach(c => {
        c.addEventListener("click", () => {
          if (!this.sel) {
            const t = new Date();
            this.sel = { y: t.getFullYear(), m: t.getMonth(), d: t.getDate(), h: 0, min: 0 };
          }
          this.sel.h = parseInt(c.dataset.h, 10);
          this.sel.min = parseInt(c.dataset.m, 10);
          this.commit(); this.renderAll();
        });
      });
    },
    renderSteppers() {
      const hourEl = $("schedDtHour"), minEl = $("schedDtMinute");
      if (!this.sel) {
        if (hourEl) hourEl.textContent = "--";
        if (minEl) minEl.textContent = "--";
      } else {
        const h12 = ((this.sel.h + 11) % 12) + 1;
        if (hourEl) hourEl.textContent = String(h12);
        if (minEl) minEl.textContent = String(this.sel.min).padStart(2, "0");
      }
      const isPm = this.sel && this.sel.h >= 12;
      document.querySelectorAll("#schedDtPanel [data-ampm]").forEach(b => {
        b.classList.toggle("selected", (b.dataset.ampm === "PM") === !!isPm);
      });
    },
    step(unit, delta) {
      if (!this.sel) {
        const t = new Date();
        this.sel = { y: t.getFullYear(), m: t.getMonth(), d: t.getDate(), h: 18, min: 0 };
      }
      if (unit === "hour") {
        this.sel.h = (this.sel.h + delta + 24) % 24;
      } else if (unit === "minute") {
        // Snap to 15-min increments
        let m = this.sel.min + delta;
        if (m >= 60) { m -= 60; this.sel.h = (this.sel.h + 1) % 24; }
        if (m < 0)   { m += 60; this.sel.h = (this.sel.h + 23) % 24; }
        this.sel.min = m;
      }
      this.commit(); this.renderAll();
    },
    setAmPm(target) {
      if (!this.sel) {
        const t = new Date();
        this.sel = { y: t.getFullYear(), m: t.getMonth(), d: t.getDate(), h: target === "PM" ? 18 : 8, min: 0 };
      } else {
        const isPm = this.sel.h >= 12;
        if (target === "PM" && !isPm) this.sel.h += 12;
        if (target === "AM" && isPm)  this.sel.h -= 12;
      }
      this.commit(); this.renderAll();
    },
    refreshFromHidden() {
      const v = ($("schedTime") || {}).value;
      const parsed = this.parseLocal(v);
      if (parsed) {
        this.sel = parsed;
        this.viewY = this.sel.y; this.viewM = this.sel.m;
      } else {
        this.sel = null;
      }
      this.renderAll();
    },
  };

  // ---- activation ----
  function activate() {
    if (state.activated) { fetchQueue(); return; }
    state.activated = true;

    wireSubTabs();

    // Init the custom datetime picker (this also seeds a default value if none).
    dtPicker.bind();

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

    // Queue detail modal -- close on X / Esc / backdrop click
    const qdClose = $("schedQueueDetailClose");
    if (qdClose) qdClose.addEventListener("click", closeDetail);
    const qdOverlay = $("schedQueueDetail");
    if (qdOverlay) qdOverlay.addEventListener("click", (e) => {
      if (e.target === qdOverlay) closeDetail();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && state.detailItemId) closeDetail();
    });

    // Bank modal
    const closeBtn = $("schedBankClose");
    if (closeBtn) closeBtn.addEventListener("click", closeBank);
    const back = $("schedBankModal");
    if (back) back.addEventListener("click", (e) => { if (e.target === back) closeBank(); });
    document.querySelectorAll(".sched-modal-toolbar .sched-chip").forEach(c => {
      c.addEventListener("click", async () => {
        document.querySelectorAll(".sched-modal-toolbar .sched-chip").forEach(x => x.classList.remove("on"));
        c.classList.add("on");
        const prev = state.bankFilter;
        state.bankFilter = c.dataset.filter;
        // Refresh bank when entering or leaving the archived view (server has different result set)
        if (state.bankFilter === "archived" || prev === "archived") {
          await refreshBank();
          populateModelDropdown();
        }
        renderBank();
      });
    });
    const search = $("schedBankSearch");
    if (search) search.addEventListener("input", () => { state.bankSearch = search.value; renderBank(); });
    const modelSel = $("schedBankModel");
    if (modelSel) modelSel.addEventListener("change", () => { state.bankModel = modelSel.value; renderBank(); });
    const sortSel = $("schedBankSort");
    if (sortSel) sortSel.addEventListener("change", () => { state.bankSort = sortSel.value; renderBank(); });
    // Zoom slider -- adjusts thumbnail size via CSS var. Persists in localStorage.
    const zoom = $("schedBankZoom");
    if (zoom) {
      const stored = parseInt(localStorage.getItem("sched-bank-zoom") || "", 10);
      if (!isNaN(stored) && stored >= 80 && stored <= 280) zoom.value = String(stored);
      const applyZoom = (px) => {
        document.documentElement.style.setProperty("--sched-thumb-size", px + "px");
      };
      applyZoom(parseInt(zoom.value, 10));
      zoom.addEventListener("input", () => {
        const px = parseInt(zoom.value, 10);
        applyZoom(px);
        localStorage.setItem("sched-bank-zoom", String(px));
      });
    }

    const refreshBtn = $("schedBankRefresh");
    if (refreshBtn) refreshBtn.addEventListener("click", async () => {
      refreshBtn.disabled = true;
      const before = state.bankItems.length;
      await refreshBank();
      populateModelDropdown();
      renderBank();
      refreshBtn.disabled = false;
      const after = state.bankItems.length;
      const delta = after - before;
      const msg = delta > 0 ? `+${delta} new` : (delta < 0 ? `${delta} removed` : "No changes");
      toast(`Bank refreshed (${after} images, ${msg})`, "ok");
    });

    // Bank preview lightbox
    const pvCancel = $("schedBankPreviewCancel");
    if (pvCancel) pvCancel.addEventListener("click", closeBankPreview);
    const pvSelect = $("schedBankPreviewSelect");
    if (pvSelect) pvSelect.addEventListener("click", selectBankPreview);
    const pvFav = $("schedBankPreviewFav");
    if (pvFav) pvFav.addEventListener("click", () => {
      if (state.bankPreviewItem) toggleFavorite(state.bankPreviewItem.path);
    });
    const pvArchive = $("schedBankPreviewArchive");
    if (pvArchive) pvArchive.addEventListener("click", toggleArchivePreview);
    const pvDelete = $("schedBankPreviewDelete");
    if (pvDelete) pvDelete.addEventListener("click", deletePreview);
    const pvCopyPath = $("schedBankPreviewCopyPath");
    if (pvCopyPath) pvCopyPath.addEventListener("click", copyPreviewPath);
    const pvFull = $("schedBankPreviewFull");
    if (pvFull) pvFull.addEventListener("click", viewPreviewFull);
    const pvImg = $("schedBankPreviewImg");
    if (pvImg) {
      pvImg.style.cursor = "zoom-in";
      pvImg.addEventListener("click", viewPreviewFull);
    }
    const pvPrev = $("schedBankPreviewPrev");
    if (pvPrev) pvPrev.addEventListener("click", (e) => { e.stopPropagation(); navPreview("prev"); });
    const pvNext = $("schedBankPreviewNext");
    if (pvNext) pvNext.addEventListener("click", (e) => { e.stopPropagation(); navPreview("next"); });
    const pvOverlay = $("schedBankPreview");
    if (pvOverlay) pvOverlay.addEventListener("click", (e) => { if (e.target === pvOverlay) closeBankPreview(); });
    document.addEventListener("keydown", (e) => {
      if (!pvOverlay || !pvOverlay.classList.contains("open")) return;
      if (e.key === "Escape") closeBankPreview();
      else if (e.key === "ArrowLeft") { e.preventDefault(); navPreview("prev"); }
      else if (e.key === "ArrowRight") { e.preventDefault(); navPreview("next"); }
    });

    updateImageCount();
    updateCharCount();
    updateLayoutTilesEnabled();
    renderPreview();
    fetchQueue();
    if (!state.pollTimer) state.pollTimer = setInterval(fetchQueue, POLL_MS);
  }

  // Expose minimal composer state so the AI Suggest chat tab can read picked images.
  window.__schedState = state;

  // Helper: fire a custom event whenever state.images changes so AI Suggest
  // (and any future listener) can react without polling.
  function notifyImagesChanged() {
    try {
      document.dispatchEvent(new CustomEvent("sched:images-changed", {
        detail: { count: state.images.length },
      }));
    } catch (e) { /* old browsers, ignore */ }
  }
  window.__schedNotifyImages = notifyImagesChanged;

  document.addEventListener("tab:activated", (e) => {
    if (e.detail.tab === TAB) activate();
  });
})();
