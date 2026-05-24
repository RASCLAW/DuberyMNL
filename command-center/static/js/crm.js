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

  function esc(s) {
    if (s === null || s === undefined) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function statusBadge(s) {
    const map = {
      "Hot": "badge-hot",
      "Warm": "badge-warm",
      "Cold": "badge-cold",
      "Converted": "badge-converted",
      "Pending": "badge-pending",
      "Done": "badge-done",
      "Delivered": "badge-done",
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
    tbody.innerHTML = leads.map((l, i) => `
      <tr class="crm-row-clickable" data-lead-idx="${i}">
        <td class="crm-td-overflow">${esc(l.name) || '<span style="color:var(--muted)">Unknown</span>'}</td>
        <td>${statusBadge(l.status)}</td>
        <td class="crm-td-overflow">${esc(l.model_interest) || '<span style="color:var(--muted)">—</span>'}</td>
        <td>${esc(l.source) || "—"}</td>
        <td>${esc(fmtDate(l.last_contact))}</td>
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
    tbody.innerHTML = orders.map((o, i) => `
      <tr class="crm-row-clickable" data-order-idx="${i}">
        <td class="crm-td-overflow">${esc(o.name) || '<span style="color:var(--muted)">Unknown</span>'}</td>
        <td class="crm-td-overflow">${esc(o.items) || "—"}</td>
        <td>&#8369;${fmt(o.total)}</td>
        <td>${statusBadge(o.status || "Pending")}</td>
        <td>${esc(fmtDate(o.order_date))}</td>
        <td style="font-size:11px;color:var(--muted)">${esc(o.source) || "—"}</td>
      </tr>
    `).join("");
  }

  // Detail modal -------------------------------------------------------------
  function showDetail(title, fields) {
    const modal = document.getElementById("crm-detail-modal");
    const titleEl = document.getElementById("crm-detail-title");
    const contentEl = document.getElementById("crm-detail-content");
    if (!modal || !contentEl) return;
    titleEl.textContent = title;
    contentEl.innerHTML = fields
      .filter(([_, v]) => v !== null && v !== undefined && v !== "")
      .map(([k, v, extra]) => `
        <div class="crm-detail-row">
          <div class="crm-detail-key">${esc(k)}</div>
          <div class="crm-detail-val">${esc(v)}${extra || ""}</div>
        </div>`).join("");
    modal.hidden = false;
  }

  function hideDetail() {
    const modal = document.getElementById("crm-detail-modal");
    if (modal) modal.hidden = true;
  }

  function mapBtn(addr) {
    if (!addr) return "";
    const q = encodeURIComponent(addr);
    return ` <a class="crm-map-btn" href="https://www.google.com/maps/search/?api=1&query=${q}" target="_blank" rel="noopener" title="Search address on Google Maps">Map</a>`;
  }

  function openLeadDetail(idx) {
    const l = leads[idx];
    if (!l) return;
    showDetail(`Lead — ${l.name || "Unknown"}`, [
      ["Name", l.name],
      ["Status", l.status],
      ["Phone", l.phone],
      ["Address", l.address, mapBtn(l.address)],
      ["Landmarks", l.landmarks],
      ["Model Interest", l.model_interest],
      ["Source", l.source],
      ["First Contact", fmtDate(l.first_contact)],
      ["Last Contact", fmtDate(l.last_contact)],
      ["Lead ID (PSID)", l.lead_id],
      ["Notes", l.notes],
    ]);
  }

  function openOrderDetail(idx) {
    const o = orders[idx];
    if (!o) return;
    showDetail(`Order — ${o.name || "Unknown"}`, [
      ["Name", o.name],
      ["Status", o.status],
      ["Date", fmtDate(o.order_date)],
      ["Items", o.items],
      ["Quantity", o.quantity],
      ["Total", "₱" + fmt(o.total)],
      ["Delivery Fee", o.delivery_fee],
      ["Payment", o.payment_method],
      ["Phone", o.phone],
      ["Address", o.address, mapBtn(o.address)],
      ["Source", o.source],
      ["Notes", o.notes],
      ["Order ID", o.order_id],
    ]);
  }

  async function loadSummary(fresh) {
    const statusEl = document.getElementById("crm-status");
    try {
      const r = await fetch("/api/crm/summary" + (fresh ? "?fresh=1" : ""));
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
      set("crm-tile-orders-sub", (d.orders_today ?? "--") + " in last 24h");
      set("crm-tile-revenue", "₱" + fmt(d.total_revenue));
      set("crm-tile-today", d.orders_today ?? "--");
      set("crm-tile-units-30d", fmt(d.units_sold_30d ?? "--"));
      if (statusEl) statusEl.textContent = "Updated " + new Date().toLocaleTimeString();
    } catch (e) {
      if (statusEl) statusEl.textContent = "CRM load failed";
    }
  }

  async function loadLeads(fresh) {
    try {
      const r = await fetch("/api/crm/leads" + (fresh ? "?fresh=1" : ""));
      const d = await r.json();
      if (d.error || !Array.isArray(d)) return;
      leads = d;
      renderLeads();
    } catch (e) { }
  }

  async function loadOrders(fresh) {
    try {
      const r = await fetch("/api/crm/orders" + (fresh ? "?fresh=1" : ""));
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

  function loadAll(fresh) {
    loadSummary(fresh);
    loadLeads(fresh);
    loadOrders(fresh);
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
    if (refresh) refresh.addEventListener("click", () => loadAll(true));

    // Row click -> detail modal (delegated so we don't re-bind after every render)
    document.addEventListener("click", function (e) {
      const row = e.target.closest("tr.crm-row-clickable");
      if (!row) return;
      if (row.dataset.leadIdx !== undefined) openLeadDetail(parseInt(row.dataset.leadIdx, 10));
      else if (row.dataset.orderIdx !== undefined) openOrderDetail(parseInt(row.dataset.orderIdx, 10));
    });
    const closeBtn = document.getElementById("crm-detail-close");
    if (closeBtn) closeBtn.addEventListener("click", hideDetail);
    const modal = document.getElementById("crm-detail-modal");
    if (modal) modal.addEventListener("click", function (e) {
      if (e.target === modal) hideDetail();  // click backdrop to close
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") hideDetail();
    });
  });
})();
