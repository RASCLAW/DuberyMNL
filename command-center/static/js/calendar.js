// Content Calendar ("Moment Engine") tab — reads/writes the content_calendar Sheet
// via /api/calendar. Suggest -> approve flow; RA approves angles here.
(function () {
  "use strict";

  let moments = [];
  let filter = "upcoming";
  const SOON_DAYS = 60;

  const TYPE_LABEL = { holiday: "Holiday", event: "Event", trend: "Trend", weather: "Weather" };

  function esc(s) {
    if (s === null || s === undefined) return "";
    return String(s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function asDate(s) {
    if (!s) return null;
    const d = new Date(String(s).trim() + "T00:00:00");
    return isNaN(d.getTime()) ? null : d;
  }

  function today0() {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }

  function classify(m) {
    const t = today0();
    const start = asDate(m.window_start);
    const end = asDate(m.window_end) || start;
    if (!start) return "unscheduled";
    if (start <= t && (end || start) >= t) return "live";
    if (start > t) {
      const diff = (start - t) / 86400000;
      return diff <= SOON_DAYS ? "soon" : "later";
    }
    return "past";
  }

  function daysUntil(m) {
    const start = asDate(m.window_start);
    if (!start) return null;
    return Math.round((start - today0()) / 86400000);
  }

  function monthKey(m) {
    const d = asDate(m.window_start);
    if (!d) return "Undated";
    return d.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  }

  function passesFilter(m) {
    const status = (m.status || "").toLowerCase();
    if (status === "dismissed" && filter !== "all") return false;
    const phase = classify(m);
    switch (filter) {
      case "upcoming": return phase === "live" || phase === "soon";
      case "live": return phase === "live";
      case "suggested": return status === "suggested";
      case "approved": return status === "approved";
      case "all": return true;
      default: return true;
    }
  }

  function statusBadge(status) {
    const s = (status || "suggested").toLowerCase();
    const map = {
      suggested: ["cal-badge-suggested", "Suggested"],
      approved: ["cal-badge-approved", "Approved"],
      generated: ["cal-badge-generated", "Generated"],
      posted: ["cal-badge-posted", "Posted"],
      dismissed: ["cal-badge-dismissed", "Dismissed"],
    };
    const [cls, label] = map[s] || ["cal-badge-suggested", status || "Suggested"];
    return `<span class="cal-badge ${cls}">${esc(label)}</span>`;
  }

  function actions(m) {
    const s = (m.status || "suggested").toLowerCase();
    const id = esc(m.id);
    if (s === "suggested") {
      return `<button class="btn cal-btn-approve" data-act="approved" data-id="${id}">Approve</button>
              <button class="btn cal-btn-ghost" data-act="dismissed" data-id="${id}">Dismiss</button>`;
    }
    if (s === "approved") {
      return `<span class="cal-approved-note">✓ Greenlit</span>
              <button class="btn cal-btn-ghost" data-act="suggested" data-id="${id}">Unapprove</button>`;
    }
    if (s === "dismissed") {
      return `<button class="btn cal-btn-ghost" data-act="suggested" data-id="${id}">Restore</button>`;
    }
    return "";
  }

  function relPip(rel) {
    const n = parseInt(rel, 10);
    if (isNaN(n)) return "";
    const cls = n >= 8 ? "rel-high" : (n >= 5 ? "rel-mid" : "rel-low");
    return `<span class="cal-rel ${cls}" title="Relevance ${n}/10">${n}</span>`;
  }

  function card(m) {
    const type = (m.type || "").toLowerCase();
    const phase = classify(m);
    const du = daysUntil(m);
    let lead = "";
    if (phase === "live") lead = `<span class="cal-live-dot">● live now</span>`;
    else if (du !== null && du >= 0) lead = `<span class="cal-lead">in ${du}d</span>`;
    const window = `${esc(m.window_start || "?")} → ${esc(m.window_end || "?")}`;
    return `
      <div class="cal-card cal-type-${esc(type)}" data-id="${esc(m.id)}">
        <div class="cal-card-top">
          <span class="cal-type-chip cal-type-${esc(type)}">${esc(TYPE_LABEL[type] || type || "—")}</span>
          ${relPip(m.relevance)}
          ${statusBadge(m.status)}
          <span class="cal-window">${window}</span>
          ${lead}
        </div>
        <div class="cal-card-title">${esc(m.title || "(untitled)")}</div>
        <div class="cal-card-angle">${esc(m.angle || "")}</div>
        <div class="cal-card-foot">
          <span class="cal-meta">${esc(m.format || "")}${m.source ? " · " + esc(m.source) : ""}${m.notes ? " · " + esc(m.notes) : ""}</span>
          <span class="cal-card-actions">${actions(m)}</span>
        </div>
      </div>`;
  }

  function render() {
    const list = document.getElementById("calendar-list");
    if (!list) return;
    const rows = moments.filter(passesFilter).sort((a, b) =>
      (a.window_start || "9999").localeCompare(b.window_start || "9999"));

    if (!rows.length) {
      list.innerHTML = `<div class="cal-empty">No moments match "${esc(filter)}".</div>`;
      return;
    }

    // group by month
    const groups = {};
    rows.forEach(m => { const k = monthKey(m); (groups[k] = groups[k] || []).push(m); });

    list.innerHTML = Object.keys(groups).map(month => `
      <div class="cal-month">${esc(month)}</div>
      ${groups[month].map(card).join("")}
    `).join("");
  }

  function renderTiles() {
    const live = moments.filter(m => classify(m) === "live" && (m.status || "") !== "dismissed").length;
    const soon = moments.filter(m => classify(m) === "soon" && (m.status || "") !== "dismissed").length;
    const review = moments.filter(m => (m.status || "").toLowerCase() === "suggested"
      && ["live", "soon"].includes(classify(m))).length;
    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    set("cal-tile-live", live);
    set("cal-tile-soon", soon);
    set("cal-tile-review", review);
  }

  async function load(fresh) {
    const statusEl = document.getElementById("calendar-status");
    try {
      const r = await fetch("/api/calendar" + (fresh ? "?fresh=1" : ""));
      const d = await r.json();
      if (!Array.isArray(d)) {
        if (statusEl) statusEl.textContent = (d && d.error) ? ("error: " + d.error) : "load failed";
        return;
      }
      moments = d;
      renderTiles();
      render();
      if (statusEl) statusEl.textContent = `${moments.length} moments · updated ${new Date().toLocaleTimeString()}`;
    } catch (e) {
      if (statusEl) statusEl.textContent = "load failed";
    }
  }

  async function setStatus(id, status) {
    try {
      const r = await fetch("/api/calendar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: id, status: status }),
      });
      const d = await r.json();
      if (!d.ok) { if (window.toast) toast("Update failed: " + (d.error || "?"), "error"); return; }
      if (window.toast) toast("Moment " + status, "ok");
      await load(true);
    } catch (e) {
      if (window.toast) toast("Update failed", "error");
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    const tab = document.querySelector('.tab[data-tab="calendar"]');
    if (tab && tab.classList.contains("active")) load();
    document.addEventListener("tab:activated", function (e) {
      if (e.detail && e.detail.tab === "calendar") load();
    });

    const refresh = document.getElementById("calendar-refresh");
    if (refresh) refresh.addEventListener("click", () => load(true));

    // Filter chips (delegated)
    document.addEventListener("click", function (e) {
      const fb = e.target.closest(".cal-filter");
      if (fb) {
        document.querySelectorAll(".cal-filter").forEach(b => b.classList.remove("active"));
        fb.classList.add("active");
        filter = fb.dataset.filter || "upcoming";
        render();
        return;
      }
      const ab = e.target.closest("[data-act]");
      if (ab && ab.dataset.id) {
        ab.disabled = true;
        setStatus(ab.dataset.id, ab.dataset.act);
      }
    });
  });

  window.__calendar = { load };
})();
