// Home tab: fetch /api/home/summary on activate + every 60s while active.
(function () {
  "use strict";

  const POLL_MS = 60_000;
  let timer = null;

  function fmtMoney(n) {
    if (n === null || n === undefined) return "--";
    try { return "₱" + Number(n).toLocaleString("en-PH"); }
    catch (e) { return String(n); }
  }

  function setText(sel, txt) {
    document.querySelectorAll(`[data-tile="${sel}"]`).forEach(el => { el.textContent = txt; });
  }

  function setPill(state) {
    const el = document.querySelector('[data-tile="system_health_pill"]');
    if (!el) return;
    el.classList.remove("green", "yellow", "red");
    let label = "—";
    if (state === "green") { el.classList.add("green"); label = "● ALL GOOD"; }
    else if (state === "yellow") { el.classList.add("yellow"); label = "● DEGRADED"; }
    else if (state === "red") { el.classList.add("red"); label = "● ATTENTION"; }
    el.textContent = label;
  }

  async function fetchSummary() {
    try {
      const res = await fetch("/api/home/summary", { cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();

      setText("revenue_today", fmtMoney(data.revenue_today));
      setText("revenue_today_sub",
        data.revenue_today === null ? "not wired (Phase 3)" : "today so far"
      );

      setText("active_convos",
        data.active_convos === null ? "--" : String(data.active_convos));
      setText("active_convos_sub",
        data.active_convos === null ? "chatbot /status check" : "live conversations"
      );

      setText("pending_approvals",
        data.pending_approvals === null ? "--" : String(data.pending_approvals));
      setText("pending_approvals_sub",
        data.pending_approvals === null ? "pipeline.json not found" : "captions + images"
      );

      setPill(data.system_health || "yellow");
      setText("system_health_sub", "across 8 monitored services");
    } catch (e) {
      setText("revenue_today", "--");
      setText("active_convos", "--");
      setText("pending_approvals", "--");
      setPill("red");
      setText("system_health_sub", "fetch failed: " + e.message);
    }
  }

  function start() {
    fetchSummary();
    if (timer) clearInterval(timer);
    timer = setInterval(fetchSummary, POLL_MS);
  }
  function stop() {
    if (timer) { clearInterval(timer); timer = null; }
  }

  document.addEventListener("tab:activated", ev => {
    if (ev.detail && ev.detail.tab === "home") start();
    else stop();
  });
})();
