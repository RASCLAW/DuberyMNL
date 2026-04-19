// Shell routing: hash-based tab switching + custom "tab:activated" event.
(function () {
  "use strict";

  const DEFAULT_TAB = "home";
  const KNOWN_TABS = [
    "home", "content-gen", "marketing", "crm",
    "chatbot", "monitor", "image-bank", "inventory"
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

  document.addEventListener("DOMContentLoaded", () => {
    // If hash missing, nudge to #home so deep-links work.
    if (!location.hash) {
      location.replace("#" + DEFAULT_TAB);
    }
    activate(currentTab());
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

  document.addEventListener("DOMContentLoaded", () => {
    pollAgentStatus();
    setInterval(pollAgentStatus, AGENT_POLL_MS);
  });

  // Expose for debugging
  window.__shell = { activate, currentTab, pollAgentStatus };
})();
