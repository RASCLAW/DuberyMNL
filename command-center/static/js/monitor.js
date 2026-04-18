// Monitor tab: render rows, hybrid polling, per-row logs modal, fix buttons + toasts.
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
    if (!iso) return "\u2014";
    var then = new Date(iso).getTime();
    if (isNaN(then)) return iso;
    var s = Math.max(0, Math.floor((Date.now() - then) / 1000));
    if (s < 60) return s + "s ago";
    var m = Math.floor(s / 60);
    if (m < 60) return m + "m ago";
    var h = Math.floor(m / 60);
    if (h < 24) return h + "h " + (m % 60) + "m ago";
    var d = Math.floor(h / 24);
    return d + "d ago";
  }

  function renderRow(r) {
    var row = document.createElement("div");
    row.className = "monitor-row" + (r.state === "not_wired" ? " dimmed" : "");

    var btns = '';
    if (r.has_fix) {
      btns += '<button class="btn btn-fix fix-btn" data-service="' + r.name + '" title="' + escapeAttr(r.fix_label || "Fix") + '">Fix</button>';
    }
    btns += '<button class="btn btn-accent logs-btn" data-service="' + r.name + '" ' + (r.state === "not_wired" ? "disabled" : "") + '>logs</button>';

    row.innerHTML =
      '<div class="monitor-left">' +
        '<div class="status-dot ' + r.state + '"></div>' +
        '<div class="service-name">' + (DISPLAY_NAMES[r.name] || r.name) + '</div>' +
        '<div class="service-meta" data-ago="' + (r.last_checked || "") + '" title="' + escapeAttr(r.message || "") + '">' + fmtAgo(r.last_checked) + (r.message ? " \u00B7 " + escapeText(r.message) : "") + '</div>' +
      '</div>' +
      '<div class="monitor-actions">' + btns + '</div>';
    return row;
  }

  function escapeText(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];
    });
  }
  function escapeAttr(s) { return escapeText(s); }

  function renderAll(results) {
    lastResults = results;
    var root = document.getElementById("monitor-list");
    if (!root) return;
    var frag = document.createDocumentFragment();
    for (var i = 0; i < results.length; i++) frag.appendChild(renderRow(results[i]));
    root.innerHTML = "";
    root.appendChild(frag);

    var lastPoll = document.getElementById("monitor-last-poll");
    if (lastPoll) lastPoll.textContent = "polled " + new Date().toLocaleTimeString();
  }

  function renderError(msg) {
    var root = document.getElementById("monitor-list");
    if (!root) return;
    root.innerHTML =
      '<div class="monitor-row">' +
        '<div class="monitor-left">' +
          '<div class="status-dot offline"></div>' +
          '<div class="service-name">Fetch failed</div>' +
          '<div class="service-meta">' + escapeText(msg) + '</div>' +
        '</div>' +
        '<button class="btn btn-accent" id="monitor-retry">retry</button>' +
      '</div>';
    var btn = document.getElementById("monitor-retry");
    if (btn) btn.addEventListener("click", function () { fetchStatus(false); });
  }

  async function fetchStatus(includeExpensive) {
    var url = "/api/monitor/status" + (includeExpensive ? "?include_expensive=1" : "");
    try {
      var res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      var data = await res.json();
      renderAll(data);
    } catch (e) {
      renderError(e.message);
    }
  }

  // Re-render timestamps every 10s without a fetch
  setInterval(function () {
    document.querySelectorAll(".monitor-row .service-meta[data-ago]").forEach(function (el) {
      var iso = el.dataset.ago;
      if (!iso) return;
      var r = lastResults.find(function (x) { return (x.last_checked || "") === iso; });
      var msg = r && r.message ? " \u00B7 " + escapeText(r.message) : "";
      el.innerHTML = fmtAgo(iso) + msg;
    });
  }, 10_000);

  // --- Fix button handler ---
  async function fixService(service) {
    var fixBtn = document.querySelector('.fix-btn[data-service="' + service + '"]');
    if (fixBtn) {
      fixBtn.disabled = true;
      fixBtn.textContent = "Fixing...";
    }

    try {
      var res = await fetch("/api/monitor/fix/" + encodeURIComponent(service), {
        method: "POST",
      });
      var data = await res.json();
      if (data.ok) {
        window.showToast(data.message || "Fix applied", "ok");
        // Re-poll after a short delay to see the effect
        setTimeout(function () { fetchStatus(false); }, 3000);
      } else {
        window.showToast(data.error || "Fix failed", "bad");
      }
    } catch (e) {
      window.showToast("Fix request failed: " + e.message, "bad");
    }

    if (fixBtn) {
      fixBtn.disabled = false;
      fixBtn.textContent = "Fix";
    }
  }

  async function openLogs(service) {
    var modal = document.getElementById("log-modal");
    var title = document.getElementById("log-modal-title");
    var source = document.getElementById("log-modal-source");
    var pre = document.getElementById("log-modal-pre");
    if (!modal) return;
    title.textContent = (DISPLAY_NAMES[service] || service) + " \u2014 logs";
    source.textContent = "loading\u2026";
    pre.textContent = "loading\u2026";
    modal.classList.remove("hidden");

    try {
      var res = await fetch("/api/monitor/logs/" + encodeURIComponent(service));
      var data = await res.json();
      source.textContent = data.source || "(no log file)";
      pre.textContent = (data.lines || []).join("\n") || "(empty)";
    } catch (e) {
      pre.textContent = "Fetch failed: " + e.message;
    }
  }

  function closeLogs() {
    var modal = document.getElementById("log-modal");
    if (modal) modal.classList.add("hidden");
  }

  // Delegate clicks
  document.addEventListener("click", function (ev) {
    var fixBtn = ev.target.closest(".fix-btn");
    if (fixBtn && !fixBtn.disabled) {
      fixService(fixBtn.dataset.service);
      return;
    }
    var logsBtn = ev.target.closest(".logs-btn");
    if (logsBtn && !logsBtn.disabled) {
      openLogs(logsBtn.dataset.service);
      return;
    }
    if (ev.target.id === "log-modal-close") closeLogs();
    if (ev.target.id === "log-modal") closeLogs();
    if (ev.target.id === "monitor-refresh-expensive") fetchStatus(true);
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") closeLogs();
  });

  function start() {
    fetchStatus(false);
    if (timer) clearInterval(timer);
    timer = setInterval(function () { fetchStatus(false); }, CHEAP_POLL_MS);
  }
  function stop() {
    if (timer) { clearInterval(timer); timer = null; }
  }

  document.addEventListener("tab:activated", function (ev) {
    if (ev.detail && ev.detail.tab === "monitor") start();
    else stop();
  });
})();
