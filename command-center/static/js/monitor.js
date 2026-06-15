// Monitor tab: render rows, hybrid polling, per-row logs modal, fix buttons + toasts.
(function () {
  "use strict";

  const CHEAP_POLL_MS = 30_000;
  let timer = null;
  let lastResults = [];

  const DISPLAY_NAMES = {
    chatbot: "Messenger Bot",
    chatbot_monitor: "Chatbot Watchdog",
    tunnel: "Cloudflare Tunnel",
    worker_fallback: "Worker Fallback",
    meta_ads: "Facebook Ads",
    story_rotation: "Story Posts",
    rasclaw_tg: "Rasclaw Notifications",
    chatbot_tg: "Order Notifications",
    crm_sheet: "Google Sheet (CRM)",
    inventory: "Inventory",
  };

  const SERVICE_DESCRIPTIONS = {
    chatbot: "Answers customer DMs on your Facebook page",
    chatbot_monitor: "Auto-restarts the bot if it crashes",
    tunnel: "Makes chatbot.duberymnl.com reachable from the internet",
    worker_fallback: "Cloudflare backup layer — filters spam and catches downtime",
    meta_ads: "Checks if your Facebook ad campaigns are actively running",
    story_rotation: "GitHub Action that posts new stories every 4 hours",
    rasclaw_tg: "Telegram alerts for your Rasclaw project",
    chatbot_tg: "Telegram pings when customers message or place an order",
    crm_sheet: "Google Sheet where leads and orders get logged",
    inventory: "Stock level tracking — not set up yet",
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

  // Map backend state -> mockup row visuals.
  // active -> fresh, degraded -> stale, offline -> dead, not_wired -> idle/gray.
  var STATE_MAP = {
    active:    { row: "fresh-row", dot: "ok",   badge: "fresh", label: "Up",    pulse: true  },
    degraded:  { row: "stale-row", dot: "warn", badge: "stale", label: "Stale", pulse: true  },
    offline:   { row: "dead-row",  dot: "bad",  badge: "dead",  label: "Down",  pulse: true  },
    not_wired: { row: "fresh-row", dot: "gray", badge: "",      label: "Idle",  pulse: false },
  };

  // 14-dot strip. We don't keep per-sweep history, so this is an honest
  // visual band coloured by the *current* state, not fabricated history.
  function spark14(state) {
    var cls = state === "offline" ? " class=\"b\"" : state === "degraded" ? " class=\"g\"" : "";
    var html = '<span class="spark14">';
    for (var i = 0; i < 14; i++) html += '<i' + cls + '></i>';
    return html + '</span>';
  }

  function renderRow(r) {
    var m = STATE_MAP[r.state] || STATE_MAP.not_wired;
    var idle = r.state === "not_wired";

    var row = document.createElement("div");
    row.className = "mon-row " + m.row + (idle ? " dimmed" : "");

    // actions cell (Fix when available, otherwise Logs)
    var btns = '';
    if (r.has_fix) {
      btns += '<button class="btn fix fix-btn" data-service="' + escapeAttr(r.name) + '" title="' + escapeAttr(r.fix_label || "Fix") + '">Fix</button>';
    }
    btns += '<button class="btn logs-btn" data-service="' + escapeAttr(r.name) + '" ' + (idle ? "disabled" : "") + '>Logs</button>';

    var desc = SERVICE_DESCRIPTIONS[r.name] || "";
    var dotCls = "dot " + m.dot + (m.pulse ? (r.state === "offline" ? " pulse-fast" : " pulse") : "");
    var badge = m.badge
      ? '<span class="hb-state ' + m.badge + '">' + escapeText(m.label) + '</span>'
      : '<span class="pill" style="justify-self:start">' + escapeText(m.label) + '</span>';

    row.innerHTML =
      '<div class="hb-name">' +
        '<span class="' + dotCls + '"></span>' +
        '<span>' + escapeText(DISPLAY_NAMES[r.name] || r.name) +
          (desc ? '<span class="sub">' + escapeText(desc) + '</span>' : '') +
        '</span>' +
      '</div>' +
      badge +
      spark14(r.state) +
      '<span class="mon-last" data-ago="' + escapeAttr(r.last_checked || "") + '" title="' + escapeAttr(r.message || "") + '">' + fmtAgo(r.last_checked) + '</span>' +
      '<span class="mon-msg" style="font-size:10.5px; color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis">' + (r.message ? escapeText(r.message) : "") + '</span>' +
      '<span class="hb-action">' + btns + '</span>';
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
      '<div class="mon-row dead-row">' +
        '<div class="hb-name"><span class="dot bad pulse-fast"></span>' +
          '<span>Fetch failed<span class="sub">' + escapeText(msg) + '</span></span>' +
        '</div>' +
        '<span class="hb-state dead">Down</span>' +
        '<span></span><span></span><span></span>' +
        '<span class="hb-action"><button class="btn" id="monitor-retry">Retry</button></span>' +
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

  // Re-render timestamps every 10s without a fetch.
  // data-ago now rides on .mon-last (the timestamp cell of the new .mon-row).
  setInterval(function () {
    document.querySelectorAll(".mon-row .mon-last[data-ago]").forEach(function (el) {
      var iso = el.dataset.ago;
      if (!iso) return;
      el.textContent = fmtAgo(iso);
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
