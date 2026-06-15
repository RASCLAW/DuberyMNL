// Shell routing: hash-based tab switching + custom "tab:activated" event.
(function () {
  "use strict";

  const DEFAULT_TAB = "home";
  const KNOWN_TABS = [
    "home", "content-gen", "video", "marketing", "crm",
    "chatbot", "monitor", "image-bank", "video-bank", "schedule", "inventory"
  ];

  function currentTab() {
    const raw = (location.hash || "").replace(/^#/, "").trim();
    return KNOWN_TABS.includes(raw) ? raw : DEFAULT_TAB;
  }

  function activate(tab) {
    document.querySelectorAll(".nav-item").forEach(n => {
      n.classList.toggle("active", n.dataset.tab === tab);
    });
    document.querySelectorAll(".tab").forEach(t => {
      t.classList.toggle("active", t.dataset.tab === tab);
    });
    document.dispatchEvent(new CustomEvent("tab:activated", { detail: { tab } }));
  }

  function onHashChange() {
    activate(currentTab());
  }

  // ========== Sidebar collapse ==========
  const SIDEBAR_KEY = "cc.sidebar.collapsed";
  function applySidebarState(collapsed) {
    const sb = document.getElementById("sidebar");
    const tg = document.getElementById("sidebarToggle");
    if (!sb || !tg) return;
    sb.classList.toggle("collapsed", collapsed);
    tg.innerHTML = collapsed ? "&rsaquo;" : "&lsaquo;";
    tg.title = collapsed ? "Expand sidebar" : "Collapse sidebar";
  }
  function toggleSidebar() {
    const sb = document.getElementById("sidebar");
    if (!sb) return;
    const next = !sb.classList.contains("collapsed");
    try { localStorage.setItem(SIDEBAR_KEY, next ? "1" : "0"); } catch (e) {}
    applySidebarState(next);
  }

  document.addEventListener("DOMContentLoaded", () => {
    // If hash missing, nudge to #home so deep-links work.
    if (!location.hash) {
      location.replace("#" + DEFAULT_TAB);
    }
    activate(currentTab());
    // Sidebar restore + toggle wiring
    const tg = document.getElementById("sidebarToggle");
    if (tg) tg.addEventListener("click", toggleSidebar);
    let stored = "0";
    try { stored = localStorage.getItem(SIDEBAR_KEY) || "0"; } catch (e) {}
    applySidebarState(stored === "1");
  });

  window.addEventListener("hashchange", onHashChange);

  // ========== Agent liveness dot ==========
  const AGENT_STATES = ["live", "warming", "stale", "dead"];
  const AGENT_POLL_MS = 15000;

  async function pollAgentStatus() {
    // Simple model: server reachable = online (green), unreachable = offline (red).
    let state = "dead";
    let title = "Agent: offline";
    try {
      const r = await fetch("/api/agent/status", { cache: "no-store" });
      if (r.ok) {
        const data = await r.json();
        state = "live";
        if (data.last_error) title = `Agent: online · last error ${data.last_error}`;
        else title = "Agent: online";
      }
    } catch (e) {
      state = "dead";
      title = `Agent: offline (${e.message})`;
    }
    document.querySelectorAll("[data-agent-dot]").forEach(el => {
      AGENT_STATES.forEach(s => el.classList.remove(s));
      el.classList.add(state);
      el.title = title;
    });
    const label = state === "live" ? "online" : "offline";
    document.querySelectorAll("[data-agent-dot-label]").forEach(el => {
      el.textContent = label;
    });
  }

  // ========== Sidebar service dots + Monitor alert (live from /api/monitor/status) ==========
  const NAV_SVC_STATE = { active: "ok", degraded: "warn", offline: "bad", not_wired: "gray" };
  const MONITOR_POLL_MS = 60000;

  async function pollMonitor() {
    try {
      const r = await fetch("/api/monitor/status", { cache: "no-store" });
      if (!r.ok) return;
      const rows = await r.json();
      const byName = {};
      let down = 0;
      rows.forEach(s => { byName[s.name] = s.state; if (s.state === "offline") down++; });
      document.querySelectorAll("[data-nav-svc]").forEach(el => {
        const cls = NAV_SVC_STATE[byName[el.getAttribute("data-nav-svc")]] || "gray";
        el.classList.remove("ok", "warn", "bad", "gray");
        el.classList.add(cls);
      });
      const alert = document.querySelector("[data-nav-alert]");
      if (alert) {
        if (down > 0) { alert.textContent = String(down); alert.hidden = false; }
        else { alert.hidden = true; }
      }
    } catch (e) { /* keep last-known dot state */ }
  }

  document.addEventListener("DOMContentLoaded", () => {
    pollAgentStatus();
    setInterval(pollAgentStatus, AGENT_POLL_MS);
    pollMonitor();
    setInterval(pollMonitor, MONITOR_POLL_MS);
  });

  // Expose for debugging
  window.__shell = { activate, currentTab, pollAgentStatus };
})();
