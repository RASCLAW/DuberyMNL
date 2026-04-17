// Monitor tab: render rows, hybrid polling, per-row logs modal.
(function () {
  "use strict";

  const CHEAP_POLL_MS = 30_000;
  let timer = null;
  let lastResults = [];

  const DISPLAY_NAMES = {
    chatbot: "Chatbot Flask",
    tunnel: "Cloudflare Tunnel",
    worker_fallback: "Worker Fallback",
    meta_ads: "Meta Ads",
    story_rotation: "Story Rotation",
    rasclaw_tg: "Rasclaw TG Bot",
    chatbot_tg: "DuberyMNL TG Pings",
    crm_sheet: "CRM Sheet",
    inventory: "Inventory",
  };

  function fmtAgo(iso) {
    if (!iso) return "—";
    const then = new Date(iso).getTime();
    if (isNaN(then)) return iso;
    const s = Math.max(0, Math.floor((Date.now() - then) / 1000));
    if (s < 60) return s + "s ago";
    const m = Math.floor(s / 60);
    if (m < 60) return m + "m ago";
    const h = Math.floor(m / 60);
    if (h < 24) return h + "h " + (m % 60) + "m ago";
    const d = Math.floor(h / 24);
    return d + "d ago";
  }

  function renderRow(r) {
    const row = document.createElement("div");
    row.className = "monitor-row" + (r.state === "not_wired" ? " dimmed" : "");
    row.innerHTML = `
      <div class="monitor-left">
        <div class="status-dot ${r.state}"></div>
        <div class="service-name">${DISPLAY_NAMES[r.name] || r.name}</div>
        <div class="service-meta" data-ago="${r.last_checked || ""}" title="${escapeAttr(r.message || "")}">${fmtAgo(r.last_checked)}${r.message ? " · " + escapeText(r.message) : ""}</div>
      </div>
      <button class="btn btn-accent logs-btn" data-service="${r.name}" ${r.state === "not_wired" ? "disabled" : ""}>logs</button>
    `;
    return row;
  }

  function escapeText(s) {
    return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  }
  function escapeAttr(s) { return escapeText(s); }

  function renderAll(results) {
    lastResults = results;
    const root = document.getElementById("monitor-list");
    if (!root) return;
    const frag = document.createDocumentFragment();
    for (const r of results) frag.appendChild(renderRow(r));
    root.innerHTML = "";
    root.appendChild(frag);

    const lastPoll = document.getElementById("monitor-last-poll");
    if (lastPoll) lastPoll.textContent = "polled " + new Date().toLocaleTimeString();
  }

  function renderError(msg) {
    const root = document.getElementById("monitor-list");
    if (!root) return;
    root.innerHTML = `
      <div class="monitor-row">
        <div class="monitor-left">
          <div class="status-dot offline"></div>
          <div class="service-name">Fetch failed</div>
          <div class="service-meta">${escapeText(msg)}</div>
        </div>
        <button class="btn btn-accent" id="monitor-retry">retry</button>
      </div>
    `;
    const btn = document.getElementById("monitor-retry");
    if (btn) btn.addEventListener("click", () => fetchStatus(false));
  }

  async function fetchStatus(includeExpensive) {
    const url = "/api/monitor/status" + (includeExpensive ? "?include_expensive=1" : "");
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      renderAll(data);
    } catch (e) {
      renderError(e.message);
    }
  }

  // Re-render timestamps every 10s without a fetch so "12s ago" keeps ticking.
  setInterval(() => {
    document.querySelectorAll(".monitor-row .service-meta[data-ago]").forEach(el => {
      const iso = el.dataset.ago;
      if (!iso) return;
      const r = lastResults.find(x => (x.last_checked || "") === iso);
      const msg = r && r.message ? " · " + escapeText(r.message) : "";
      el.innerHTML = fmtAgo(iso) + msg;
    });
  }, 10_000);

  async function openLogs(service) {
    const modal = document.getElementById("log-modal");
    const title = document.getElementById("log-modal-title");
    const source = document.getElementById("log-modal-source");
    const pre = document.getElementById("log-modal-pre");
    if (!modal) return;
    title.textContent = (DISPLAY_NAMES[service] || service) + " — logs";
    source.textContent = "loading…";
    pre.textContent = "loading…";
    modal.classList.remove("hidden");

    try {
      const res = await fetch(`/api/monitor/logs/${encodeURIComponent(service)}`);
      const data = await res.json();
      source.textContent = data.source || "(no log file)";
      pre.textContent = (data.lines || []).join("\n") || "(empty)";
    } catch (e) {
      pre.textContent = "Fetch failed: " + e.message;
    }
  }

  function closeLogs() {
    const modal = document.getElementById("log-modal");
    if (modal) modal.classList.add("hidden");
  }

  // Delegate clicks: logs button + modal close + overlay click
  document.addEventListener("click", ev => {
    const logsBtn = ev.target.closest(".logs-btn");
    if (logsBtn && !logsBtn.disabled) {
      openLogs(logsBtn.dataset.service);
      return;
    }
    if (ev.target.id === "log-modal-close") closeLogs();
    if (ev.target.id === "log-modal") closeLogs();
    if (ev.target.id === "monitor-refresh-expensive") fetchStatus(true);
  });

  document.addEventListener("keydown", ev => {
    if (ev.key === "Escape") closeLogs();
  });

  function start() {
    fetchStatus(false);
    if (timer) clearInterval(timer);
    timer = setInterval(() => fetchStatus(false), CHEAP_POLL_MS);
  }
  function stop() {
    if (timer) { clearInterval(timer); timer = null; }
  }

  document.addEventListener("tab:activated", ev => {
    if (ev.detail && ev.detail.tab === "monitor") start();
    else stop();
  });
})();
