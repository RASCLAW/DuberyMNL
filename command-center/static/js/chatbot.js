// Chatbot tab: ports the bot's /conversations admin into the Command Center.
// Read via /api/chatbot/conversations (CC reads the store file, read-only);
// RELEASE / FLAG / MARK SALE proxy to the live chatbot on :8085.
(function () {
  "use strict";

  let convs = [];

  function esc(s) {
    if (s === null || s === undefined) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function toast(msg, type) {
    if (window.showToast) window.showToast(msg, type || "info");
  }

  function shortTime(iso) {
    if (!iso) return "";
    return esc(String(iso).slice(0, 16).replace("T", " "));
  }

  function tail6(psid) {
    return "•" + esc(psid.slice(-6));
  }

  // ---- render ----------------------------------------------------------------
  function badges(c) {
    const out = [];
    out.push(`<span class="cb-badge cb-badge-count">${c.total_messages} msg</span>`);
    if (c.handoff_flagged) {
      const reason = c.handoff_reason ? ": " + esc(c.handoff_reason) : "";
      out.push(`<span class="cb-badge cb-badge-handoff">HANDOFF${reason}</span>`);
    } else {
      out.push(`<span class="cb-badge cb-badge-active">ACTIVE</span>`);
    }
    if (c.order_recorded) {
      let t = "ORDER";
      if (c.last_order_id) t += " " + esc(c.last_order_id);
      if (c.last_order_total) t += " / ₱" + esc(c.last_order_total);
      out.push(`<span class="cb-badge cb-badge-order">${t}</span>`);
    }
    (c.policies_delivered || []).forEach(p =>
      out.push(`<span class="cb-badge cb-badge-policy">policy: ${esc(p)}</span>`));
    if (c.source_ref) out.push(`<span class="cb-badge cb-badge-source">ref: ${esc(c.source_ref)}</span>`);
    else if (c.source_ad_id) out.push(`<span class="cb-badge cb-badge-source">ad_id: ${esc(c.source_ad_id)}</span>`);
    if (c.nurture_sent) out.push(`<span class="cb-badge cb-badge-nurtured">nurtured</span>`);
    (c.detected_intents || []).forEach(i =>
      out.push(`<span class="cb-badge cb-badge-intent">${esc(i)}</span>`));
    return out.join("");
  }

  function messages(c) {
    if (!c.messages || !c.messages.length) return "";
    const rows = c.messages.map(m => {
      const manual = m.intent === "manual_sale" ? " cb-msg-manual-sale" : "";
      return `<div class="cb-msg cb-msg-${esc(m.role)}${manual}">${esc(m.content)}</div>`;
    }).join("");
    return `<div class="cb-messages">${rows}</div>`;
  }

  function actions(c) {
    const psid = esc(c.sender_id);
    let html = '<div class="cb-actions">';
    if (c.handoff_flagged) {
      html += `<button class="btn cb-btn-release" data-act="release" data-psid="${psid}">RELEASE</button>`;
    } else {
      html += `<button class="btn cb-btn-flag" data-act="flag" data-psid="${psid}">FLAG HANDOFF</button>`;
    }
    if (!c.order_recorded) {
      html += `<button class="btn btn-accent" data-act="sale-toggle" data-psid="${psid}">MARK SALE</button>`;
    }
    html += "</div>";
    return html;
  }

  function saleForm(c) {
    const psid = esc(c.sender_id);
    return `
    <div class="cb-sale-form" id="cb-sale-${psid}">
      <div class="cb-sale-row">
        <input type="text" id="cb-name-${psid}" placeholder="Customer name" value="${esc(c.first_name || "")}">
        <input type="text" id="cb-phone-${psid}" placeholder="Phone (09xxxxxxxxx)" style="max-width:160px;">
      </div>
      <div class="cb-sale-row">
        <input type="text" id="cb-address-${psid}" placeholder="Full delivery address">
      </div>
      <div class="cb-sale-row">
        <input type="text" id="cb-items-${psid}" placeholder="e.g. Bandits Green x1, Outback Red x1">
        <input type="number" id="cb-total-${psid}" placeholder="Total (PHP)" style="max-width:120px;">
      </div>
      <div class="cb-sale-row">
        <input type="text" id="cb-payment-${psid}" placeholder="Payment: COD / GCash / Bank" value="COD">
        <input type="text" id="cb-note-${psid}" placeholder="Optional note">
      </div>
      <button class="btn btn-accent" data-act="sale-record" data-psid="${psid}">RECORD SALE</button>
    </div>`;
  }

  function render() {
    const list = document.getElementById("cb-list");
    if (!list) return;
    if (!convs.length) {
      list.innerHTML = '<div class="cb-empty">No conversations yet.</div>';
      return;
    }
    list.innerHTML = convs.map(c => `
      <div class="cb-conv" data-psid="${esc(c.sender_id)}">
        <div class="cb-conv-header">
          <div>
            <span class="cb-conv-sender">${esc(c.first_name) || "Unknown"}</span>
            <span class="cb-conv-psid">${esc(c.sender_id)}</span>
          </div>
          <span class="cb-conv-time">${shortTime(c.updated_at)}</span>
        </div>
        <div class="cb-badges">${badges(c)}</div>
        ${messages(c)}
        ${actions(c)}
        ${c.order_recorded ? "" : saleForm(c)}
      </div>`).join("");
  }

  // ---- actions ---------------------------------------------------------------
  async function doRelease(psid) {
    try {
      const r = await fetch("/api/chatbot/release/" + psid, { method: "POST" });
      const j = await r.json();
      if (j.ok) { toast("Released " + tail6(psid), "success"); load(); }
      else toast(j.error || "Release failed", "error");
    } catch (e) { toast("Release error: " + e, "error"); }
  }

  async function doFlag(psid) {
    try {
      const r = await fetch("/api/chatbot/flag/" + psid, { method: "POST" });
      const j = await r.json();
      if (j.ok) { toast("Flagged " + tail6(psid), "success"); load(); }
      else toast(j.error || "Flag failed", "error");
    } catch (e) { toast("Flag error: " + e, "error"); }
  }

  function toggleSale(psid) {
    const f = document.getElementById("cb-sale-" + psid);
    if (f) f.classList.toggle("open");
  }

  async function doMarkSale(psid) {
    const val = id => (document.getElementById(id + "-" + psid) || {}).value || "";
    const items = val("cb-items").trim();
    const total = parseFloat(val("cb-total"));
    const payment = val("cb-payment").trim() || "COD";
    const note = val("cb-note").trim();
    const name = val("cb-name").trim();
    const phone = val("cb-phone").trim();
    const address = val("cb-address").trim();
    if (!items) { toast("Items required", "error"); return; }
    if (!total || total <= 0) { toast("Total must be > 0", "error"); return; }
    try {
      const r = await fetch("/api/chatbot/mark-sale/" + psid, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items, total, payment_method: payment, note, name, phone, address }),
      });
      const j = await r.json();
      if (j.ok) { toast("Sale marked: " + j.order_id, "success"); load(); }
      else toast(j.error || "Mark-sale failed", "error");
    } catch (e) { toast("Mark-sale error: " + e, "error"); }
  }

  // ---- load ------------------------------------------------------------------
  async function load() {
    const statusEl = document.getElementById("cb-status");
    try {
      const r = await fetch("/api/chatbot/conversations");
      const d = await r.json();
      if (d.error) { if (statusEl) statusEl.textContent = "Chatbot: " + d.error; return; }
      convs = d.conversations || [];
      const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
      const s = d.stats || {};
      set("cb-tile-needs", d.needs_you ?? "--");
      set("cb-tile-in", s.messages_received ?? "--");
      set("cb-tile-out", s.messages_sent ?? "--");
      set("cb-tile-handoffs", s.handoffs_triggered ?? "--");
      set("cb-tile-nurtures", s.nurtures_sent ?? "--");
      if (statusEl) {
        const dot = d.online ? "● online" : "○ offline";
        statusEl.textContent = `${dot} · ${convs.length} shown · updated ${new Date().toLocaleTimeString()}`;
      }
      render();
    } catch (e) {
      if (statusEl) statusEl.textContent = "Chatbot load failed";
    }
  }

  // ---- wiring ----------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", function () {
    const tab = document.querySelector('.tab[data-tab="chatbot"]');
    if (tab && tab.classList.contains("active")) load();
    document.addEventListener("tab:activated", function (e) {
      if (e.detail && e.detail.tab === "chatbot") load();
    });
    const refresh = document.getElementById("cb-refresh");
    if (refresh) refresh.addEventListener("click", load);

    // Delegated card actions (survive re-render)
    document.addEventListener("click", function (e) {
      const btn = e.target.closest("[data-act]");
      if (!btn) return;
      const psid = btn.dataset.psid;
      switch (btn.dataset.act) {
        case "release": doRelease(psid); break;
        case "flag": doFlag(psid); break;
        case "sale-toggle": toggleSale(psid); break;
        case "sale-record": doMarkSale(psid); break;
      }
    });
  });
})();
