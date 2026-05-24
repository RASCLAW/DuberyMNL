// Home tab: one fetch -> /api/home/summary populates every section.
// Polls every 60s while active; stops on tab switch.
(function () {
  "use strict";

  const POLL_MS = 60_000;
  let timer = null;

  function fmtMoney(n) {
    if (n === null || n === undefined) return "--";
    try { return "₱" + Number(n).toLocaleString("en-PH", { maximumFractionDigits: 0 }); }
    catch (e) { return String(n); }
  }
  function fmtPct(n) {
    if (n === null || n === undefined) return "--";
    return Number(n).toFixed(1) + "%";
  }
  function fmtNum(n) {
    if (n === null || n === undefined) return "--";
    return String(n);
  }
  function fmtSeconds(s) {
    if (s === null || s === undefined) return "--";
    const n = Number(s);
    if (n < 60) return n + "s";
    return Math.floor(n / 60) + "m " + (n % 60) + "s";
  }
  function esc(s) {
    if (s === null || s === undefined) return "";
    return String(s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function setText(sel, txt) {
    document.querySelectorAll(`[data-tile="${sel}"]`).forEach(el => { el.textContent = txt; });
  }

  function setPill(state, msg) {
    const el = document.querySelector('[data-tile="system_health_pill"]');
    if (!el) return;
    el.classList.remove("green", "yellow", "red");
    let label = "—";
    if (state === "green") { el.classList.add("green"); label = "● ALL GOOD"; }
    else if (state === "yellow") { el.classList.add("yellow"); label = "● DEGRADED"; }
    else if (state === "red") { el.classList.add("red"); label = "● ATTENTION"; }
    el.textContent = label;
    setText("system_health_sub", msg || "");
  }

  function statusBadge(s) {
    const map = {
      "Hot": "badge-hot", "Warm": "badge-warm", "Cold": "badge-cold",
      "Converted": "badge-converted", "Pending": "badge-pending",
      "Done": "badge-done", "Delivered": "badge-done", "Cancelled": "badge-cancelled",
      "CANCELED": "badge-cancelled", "DELIVERED": "badge-done",
    };
    const cls = map[s] || "badge-cold";
    return `<span class="badge ${cls}">${esc(s)}</span>`;
  }

  function renderRecentOrders(orders) {
    const el = document.querySelector('[data-tile="recent_orders"]');
    if (!el) return;
    if (!orders || !orders.length) {
      el.innerHTML = '<li class="muted">No recent orders.</li>';
      return;
    }
    el.innerHTML = orders.slice(0, 3).map(o => {
      const items = String(o.items || "");
      return `
      <li class="home-recent-item">
        <div class="home-recent-item-row">
          <span class="home-recent-name">${esc(o.name)}</span>
          <span class="home-recent-amount">${fmtMoney(o.total)}</span>
        </div>
        <div class="home-recent-meta">
          ${statusBadge(o.status)}
          <span class="muted">${esc(items.slice(0, 36))}${items.length > 36 ? "…" : ""}</span>
          <span class="muted">· ${esc(o.date)}</span>
        </div>
      </li>`;
    }).join("");
  }

  function renderRecentLeads(leads) {
    const el = document.querySelector('[data-tile="recent_leads"]');
    if (!el) return;
    if (!leads || !leads.length) {
      el.innerHTML = '<li class="muted">No recent leads.</li>';
      return;
    }
    el.innerHTML = leads.slice(0, 3).map(l => `
      <li class="home-recent-item">
        <div class="home-recent-item-row">
          <span class="home-recent-name">${esc(l.name)}</span>
          ${statusBadge(l.status)}
        </div>
        <div class="home-recent-meta">
          <span class="muted">${esc(l.model_interest || "—")}</span>
          <span class="muted">· ${esc(l.source || "—")}</span>
          <span class="muted">· ${esc(l.last_contact || "—")}</span>
        </div>
      </li>
    `).join("");
  }

  function renderTopAd(a) {
    const el = document.querySelector('[data-tile="topad_card"]');
    if (!el) return;
    if (!a) {
      el.innerHTML = '<div class="muted" style="padding:20px;">No insights cached yet. Run <code>python tools/meta_ads/pull_insights.py --days 14</code>.</div>';
      return;
    }
    el.innerHTML = `
      <div class="home-topad-name">${esc(a.name)}</div>
      <div class="home-topad-grid">
        <div><span class="muted">Spend</span><b>${fmtMoney(a.spend)}</b></div>
        <div><span class="muted">LPV</span><b>${fmtNum(a.lpv)}</b></div>
        <div><span class="muted">Cost / LPV</span><b>${fmtMoney(a.cost_per_lpv)}</b></div>
        <div><span class="muted">CTR</span><b>${a.ctr ? Number(a.ctr).toFixed(2) + "%" : "--"}</b></div>
        <div><span class="muted">Messages</span><b>${fmtNum(a.messages)}</b></div>
        <div><span class="muted">Purchases (Pixel)</span><b>${fmtNum(a.purchases)}</b></div>
      </div>
      <div class="home-topad-meta muted">ad_id: ${esc(a.ad_id)}</div>
    `;
  }

  async function fetchSummary() {
    try {
      const res = await fetch("/api/home/summary", { cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const d = await res.json();

      // 1. Money
      setText("revenue_today", fmtMoney(d.revenue_today));
      setText("revenue_today_sub", d.orders_today + " order" + (d.orders_today === 1 ? "" : "s") + " today");
      setText("revenue_7d", fmtMoney(d.revenue_7d));
      setText("revenue_7d_sub", "rolling 7 days");
      setText("ads_spend_today", fmtMoney(d.ads_spend_today));
      setText("ads_spend_today_sub", d.ads_spend_total ? "~avg from 14d cache" : "no insights cached");
      setText("roas_14d", d.roas_14d ? d.roas_14d.toFixed(1) + "x" : "--");
      setText("roas_14d_sub", d.roas_14d ? "revenue / spend" : "needs ads + revenue data");

      // 2. Clarity
      const c = d.clarity || {};
      setText("clarity_sessions", fmtNum(c.sessions));
      setText("clarity_users_sub", c.users ? c.users + " unique users" : "—");
      setText("clarity_quickback", fmtPct(c.quickback_pct));
      setText("clarity_deadclick", fmtPct(c.deadclick_pct));
      setText("clarity_active", fmtSeconds(c.active_seconds));

      // 3. Needs attention
      setText("pending_approvals", fmtNum(d.pending_approvals));
      setText("scheduled_24h", fmtNum(d.scheduled_24h));
      setText("active_convos", fmtNum(d.active_convos));
      setText("orders_today", fmtNum(d.orders_today));

      // 4. Recent activity
      renderRecentOrders(d.recent_orders);
      renderRecentLeads(d.recent_leads);

      // 5. Top ad
      renderTopAd(d.top_ad);

      // 6. System health
      setPill(d.system_health || "yellow", d.system_health_msg || "");

      // status line
      const t = new Date();
      setText("home_status", "Updated " + t.toLocaleTimeString());
    } catch (e) {
      setText("home_status", "fetch failed: " + e.message);
      setPill("red", "fetch failed: " + e.message);
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
