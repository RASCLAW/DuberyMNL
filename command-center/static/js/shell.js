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

  // Expose for debugging
  window.__shell = { activate, currentTab };
})();
