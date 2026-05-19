(function () {
  "use strict";

  let leads = [], orders = [];

  function fmt(n) {
    if (n === null || n === undefined || n === "") return "--";
    const num = parseFloat(n);
    return isNaN(num) ? "--" : num.toLocaleString();
  }

  function fmtDate(iso) {
    if (!iso) return "--";
    return iso.slice(0, 10);
  }

  function statusBadge(s) {
    const map = {
      "Hot": "badge-hot",
      "Warm": "badge-warm",
      "Cold": "badge-cold",
      "Converted": "badge-converted",
      "Pending": "badge-pending",
      "Done": "badge-done",
      "Cancelled": "badge-cancelled",
    };
    const label = s || "Cold";
    const cls = map[label] || "badge-cold";
    return `<span class="badge ${cls}">${label}</span>`;
  }

  function renderLeads() {
    const tbody = document.getElementById("crm-leads-body");
    const count = document.getElementById("crm-leads-count");
    if (!tbody) return;
    count.textContent = leads.length + " leads";
    if (!leads.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="crm-empty">No leads yet</td></tr>';
      return;
    }
    tbody.innerHTML = leads.map(l => `
      <tr>
        <td class="crm-td-overflow">${l.name || '<span style="color:var(--muted)">Unknown</span>'}</td>
        <td>${statusBadge(l.status)}</td>
        <td class="crm-td-overflow">${l.model_interest || '<span style="color:var(--muted)">—</span>'}</td>
        <td>${l.source || "—"}</td>
        <td>${fmtDate(l.last_contact)}</td>
      </tr>
    `).join("");
  }

  function renderOrders() {
    const tbody = document.getElementById("crm-orders-body");
    const count = document.getElementById("crm-orders-count");
    if (!tbody) return;
    count.textContent = orders.length + " orders";
    if (!orders.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="crm-empty">No orders yet</td></tr>';
      return;
    }
    tbody.innerHTML = orders.map(o => `
      <tr>
        <td style="font-family:monospace;font-size:11px">${o.order_id || "—"}</td>
        <td class="crm-td-overflow">${o.items || "—"}</td>
        <td>&#8369;${fmt(o.total)}</td>
        <td>${o.payment_method || "—"}</td>
        <td>${statusBadge(o.status || "Pending")}</td>
        <td>${fmtDate(o.order_date)}</td>
      </tr>
    `).join("");
  }

  async function loadSummary() {
    const statusEl = document.getElementById("crm-status");
    try {
      const r = await fetch("/api/crm/summary");
      const d = await r.json();
      if (d.error) {
        if (statusEl) statusEl.textContent = "CRM: " + d.error;
        return;
      }
      const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
      set("crm-tile-leads", d.total_leads ?? "--");
      const sc = d.status_counts || {};
      set("crm-tile-leads-sub",
        `${sc.Hot || 0} hot · ${sc.Warm || 0} warm · ${sc.Cold || 0} cold · ${sc.Converted || 0} converted`);
      set("crm-tile-orders", d.total_orders ?? "--");
      set("crm-tile-orders-sub", (d.orders_today ?? "--") + " today");
      set("crm-tile-revenue", "₱" + fmt(d.total_revenue));
      set("crm-tile-today", d.orders_today ?? "--");
      if (statusEl) statusEl.textContent = "Updated " + new Date().toLocaleTimeString();
    } catch (e) {
      if (statusEl) statusEl.textContent = "CRM load failed";
    }
  }

  async function loadLeads() {
    try {
      const r = await fetch("/api/crm/leads");
      const d = await r.json();
      if (d.error || !Array.isArray(d)) return;
      leads = d;
      renderLeads();
    } catch (e) { }
  }

  async function loadOrders() {
    try {
      const r = await fetch("/api/crm/orders");
      const d = await r.json();
      if (d.error || !Array.isArray(d)) return;
      orders = d;
      renderOrders();
    } catch (e) { }
  }

  async function loadAnalytics() {
    const statusEl = document.getElementById("crm-analytics-status");
    try {
      const r = await fetch("/api/analytics/page");
      const d = await r.json();
      if (d.error) {
        if (statusEl) statusEl.textContent = d.error;
        return;
      }
      if (statusEl) statusEl.textContent = "7-day totals";

      const setMetric = (id, key) => {
        const el = document.getElementById(id);
        if (el) el.textContent = d[key] ? fmt(d[key].total) : "--";
      };
      setMetric("crm-m-fans", "fans");
      setMetric("crm-m-talking", "talking_about");
      setMetric("crm-m-impressions", "page_impressions_unique");
      setMetric("crm-m-engagement", "page_post_engagements");
      setMetric("crm-m-views", "page_views_total");
    } catch (e) {
      if (statusEl) statusEl.textContent = "analytics load failed";
    }
  }

  function loadAll() {
    loadSummary();
    loadLeads();
    loadOrders();
    loadAnalytics();
  }

  document.addEventListener("DOMContentLoaded", function () {
    const crm = document.querySelector('.tab[data-tab="crm"]');
    if (crm && crm.classList.contains("active")) {
      loadAll();
    }
    document.addEventListener("tab:activated", function (e) {
      if (e.detail && e.detail.tab === "crm") loadAll();
    });
    const refresh = document.getElementById("crm-refresh");
    if (refresh) refresh.addEventListener("click", loadAll);
  });
})();
