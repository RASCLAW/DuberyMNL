// Schedule -> Calendar tab. Builds a month grid from /api/schedule/calendar.
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const PHT_OFFSET_MIN = 8 * 60;

  const state = {
    monthYYYYMM: null,  // "YYYY-MM"
    today: null,        // "YYYY-MM-DD" PHT
    selected: null,     // "YYYY-MM-DD" or null
    data: null,         // last fetch
    wired: false,
  };

  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  }

  function todayPhtYMD() {
    // PHT date now, derived from UTC + 8h
    const d = new Date(Date.now() + PHT_OFFSET_MIN * 60000);
    return d.toISOString().slice(0, 10);
  }

  function thisMonthPHT() {
    return todayPhtYMD().slice(0, 7);
  }

  function shiftMonth(yyyymm, delta) {
    const [y, m] = yyyymm.split("-").map(Number);
    const d = new Date(Date.UTC(y, m - 1 + delta, 1));
    return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
  }

  function monthTitle(yyyymm) {
    const [y, m] = yyyymm.split("-").map(Number);
    const d = new Date(Date.UTC(y, m - 1, 1));
    return d.toLocaleString("en-US", { month: "long", year: "numeric", timeZone: "UTC" });
  }

  // Mon=0..Sun=6 (PHT-style week start on Monday like mockup)
  function isoWeekday(year, month, day) {
    const d = new Date(Date.UTC(year, month - 1, day));
    return (d.getUTCDay() + 6) % 7;
  }

  function buildCells(yyyymm) {
    const [year, month] = yyyymm.split("-").map(Number);
    const firstWd = isoWeekday(year, month, 1);
    const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate();
    const cells = [];

    // Previous-month tail
    if (firstWd > 0) {
      const prevDays = new Date(Date.UTC(year, month - 1, 0)).getUTCDate();
      for (let i = firstWd - 1; i >= 0; i--) {
        const d = prevDays - i;
        const pm = month === 1 ? 12 : month - 1;
        const py = month === 1 ? year - 1 : year;
        cells.push({ y: py, m: pm, d, other: true });
      }
    }
    // This month
    for (let d = 1; d <= daysInMonth; d++) cells.push({ y: year, m: month, d, other: false });
    // Next-month head to fill the grid
    while (cells.length % 7 !== 0) {
      const lastIdx = cells.length;
      const prev = cells[lastIdx - 1];
      const nm = prev.m === 12 ? 1 : prev.m + 1;
      const ny = prev.m === 12 ? prev.y + 1 : prev.y;
      const offset = lastIdx - (firstWd + daysInMonth) + 1;
      cells.push({ y: ny, m: nm, d: offset, other: true });
    }
    // Always show 6 rows max for stability (42 cells)
    while (cells.length < 42) {
      const last = cells[cells.length - 1];
      const nm = last.m === 12 ? 1 : last.m + 1;
      const ny = last.m === 12 ? last.y + 1 : last.y;
      const nd = last.d + 1;
      cells.push({ y: ny, m: nm, d: nd, other: true });
    }
    return cells;
  }

  function dateStrOf(c) {
    return `${c.y}-${String(c.m).padStart(2, "0")}-${String(c.d).padStart(2, "0")}`;
  }

  function render() {
    if (!state.data) return;
    $("schedCalTitle").textContent = monthTitle(state.monthYYYYMM);
    const grid = $("schedCalGrid");
    if (!grid) return;
    const cells = buildCells(state.monthYYYYMM);
    const days = state.data.days || {};

    grid.innerHTML = cells.map(c => {
      const dStr = dateStrOf(c);
      const slot = days[dStr] || {};
      const isToday = dStr === state.today;
      const isSelected = dStr === state.selected;
      const classes = ["sched-cal-cell"];
      if (c.other) classes.push("other");
      if (isToday) classes.push("today");
      if (isSelected) classes.push("selected");

      let chips = "";
      (slot.holidays || []).forEach(h => {
        chips += `<div class="sched-cal-chip holiday" title="${escapeHtml(h.name)}">${escapeHtml(h.name)}</div>`;
      });
      (slot.events || []).forEach(e => {
        chips += `<div class="sched-cal-chip event" title="${escapeHtml(e.title)}${e.notes ? ' -- ' + escapeHtml(e.notes) : ''}">${escapeHtml(e.title)}</div>`;
      });

      let posts = "";
      (slot.posts || []).slice(0, 4).forEach(p => {
        const kind = (p.status === "POSTED") ? "posted" : (p.status === "FAILED" ? "failed" : "");
        const cap = (p.caption || "").slice(0, 40);
        posts += `<div class="sched-cal-post ${kind}" title="${escapeHtml(p.time)} -- ${escapeHtml(cap)}">
          <span class="sched-cal-post-time">${escapeHtml(p.time)}</span>
          <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(cap)}</span>
        </div>`;
      });
      const overflowN = (slot.posts || []).length - 4;
      if (overflowN > 0) posts += `<div class="small muted" style="margin-top:2px">+${overflowN} more</div>`;

      return `<div class="${classes.join(' ')}" data-date="${dStr}">
        <div class="sched-cal-date">${c.d}</div>
        ${chips}
        ${posts}
      </div>`;
    }).join("");

    // wire cell handlers
    grid.querySelectorAll(".sched-cal-cell").forEach(cell => {
      cell.addEventListener("click", () => selectDay(cell.dataset.date));
      cell.addEventListener("mouseenter", (e) => showTooltip(e.currentTarget));
      cell.addEventListener("mouseleave", hideTooltip);
    });

    // render selection panel
    renderSelectedPanel();
  }

  function renderSelectedPanel() {
    const label = $("schedCalSelLabel");
    const body = $("schedCalSelBody");
    if (!label || !body) return;
    if (!state.selected) {
      label.textContent = "Selected: hover or click a day";
      body.className = "sched-cal-sel-body";
      body.innerHTML = "Click any date to see scheduled posts, holidays, and PH events for that day.";
      return;
    }
    const slot = (state.data && state.data.days && state.data.days[state.selected]) || { posts: [], events: [], holidays: [] };
    const niceDate = new Date(state.selected + "T00:00:00+08:00").toLocaleDateString("en-PH", { weekday: "long", month: "long", day: "numeric", year: "numeric", timeZone: "Asia/Manila" });
    label.textContent = niceDate;
    body.className = "sched-cal-sel-body has-content";
    let html = "";
    if (slot.holidays && slot.holidays.length) {
      html += `<div class="sched-cal-sel-section"><h4>Holidays</h4><ul>` +
        slot.holidays.map(h => `<li>${escapeHtml(h.name)}</li>`).join("") + `</ul></div>`;
    }
    if (slot.events && slot.events.length) {
      html += `<div class="sched-cal-sel-section"><h4>Events</h4><ul>` +
        slot.events.map(e => `<li>${escapeHtml(e.title)}${e.notes ? ` <span class="meta">-- ${escapeHtml(e.notes)}</span>` : ""}</li>`).join("") + `</ul></div>`;
    }
    if (slot.posts && slot.posts.length) {
      html += `<div class="sched-cal-sel-section"><h4>Scheduled posts</h4><ul>` +
        slot.posts.map(p => {
          const tag = `[${p.status || "?"}]`;
          return `<li><strong>${escapeHtml(p.time)}</strong> ${escapeHtml(p.caption || "(no caption)")} <span class="meta">${tag} ${p.image_count}x</span></li>`;
        }).join("") + `</ul></div>`;
    }
    if (!html) html = `<span class="muted" style="font-style:italic">No posts, holidays, or events on this day.</span>`;
    body.innerHTML = html;
  }

  function selectDay(dateStr) {
    state.selected = dateStr;
    // Toggle .selected class on cells without re-rendering grid
    document.querySelectorAll(".sched-cal-cell.selected").forEach(c => c.classList.remove("selected"));
    const cell = document.querySelector(`.sched-cal-cell[data-date="${dateStr}"]`);
    if (cell) cell.classList.add("selected");
    renderSelectedPanel();
  }

  function showTooltip(cell) {
    const dStr = cell.dataset.date;
    const slot = (state.data && state.data.days && state.data.days[dStr]) || null;
    if (!slot || (!(slot.holidays || []).length && !(slot.events || []).length && !(slot.posts || []).length)) return;
    const tip = $("schedCalTooltip");
    if (!tip) return;
    const parts = [];
    if ((slot.holidays || []).length) parts.push(`<strong>Holidays</strong>${slot.holidays.map(h => `<div>${escapeHtml(h.name)}</div>`).join("")}`);
    if ((slot.events || []).length) parts.push(`<strong>Events</strong>${slot.events.map(e => `<div>${escapeHtml(e.title)}</div>`).join("")}`);
    if ((slot.posts || []).length) parts.push(`<strong>Posts (${slot.posts.length})</strong>${slot.posts.map(p => `<div>${escapeHtml(p.time)} -- ${escapeHtml((p.caption || "").slice(0, 50))}</div>`).join("")}`);
    tip.innerHTML = parts.join("");
    tip.style.display = "block";
    // Position above the cell, clamp to viewport
    const r = cell.getBoundingClientRect();
    const tipRect = tip.getBoundingClientRect();
    let left = r.left + r.width / 2 - tipRect.width / 2;
    let top = r.top - tipRect.height - 8;
    if (top < 8) top = r.bottom + 8;
    left = Math.max(8, Math.min(left, window.innerWidth - tipRect.width - 8));
    tip.style.left = `${left}px`;
    tip.style.top = `${top}px`;
  }

  function hideTooltip() {
    const tip = $("schedCalTooltip");
    if (tip) tip.style.display = "none";
  }

  async function loadMonth(yyyymm) {
    state.monthYYYYMM = yyyymm;
    state.today = state.today || todayPhtYMD();
    try {
      const r = await fetch(`/api/schedule/calendar?month=${encodeURIComponent(yyyymm)}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      state.data = await r.json();
      if (state.data.today) state.today = state.data.today;
      render();
    } catch (e) {
      console.error("calendar load failed", e);
      if ($("schedCalGrid")) {
        $("schedCalGrid").innerHTML = `<div style="grid-column:1/-1;padding:20px;text-align:center;color:var(--bad)">Failed to load calendar: ${escapeHtml(e.message)}</div>`;
      }
    }
  }

  function wire() {
    if (state.wired) return;
    state.wired = true;
    const prev = $("schedCalPrev");
    if (prev) prev.addEventListener("click", () => loadMonth(shiftMonth(state.monthYYYYMM, -1)));
    const next = $("schedCalNext");
    if (next) next.addEventListener("click", () => loadMonth(shiftMonth(state.monthYYYYMM, +1)));
    const today = $("schedCalToday");
    if (today) today.addEventListener("click", () => {
      const tm = thisMonthPHT();
      const tdy = todayPhtYMD();
      if (tm !== state.monthYYYYMM) loadMonth(tm).then(() => selectDay(tdy));
      else selectDay(tdy);
    });
    window.addEventListener("scroll", hideTooltip, { passive: true });
  }

  function activate(monthYYYYMM) {
    wire();
    const target = monthYYYYMM || state.monthYYYYMM || thisMonthPHT();
    // Always refresh on activation so newly-scheduled posts appear
    loadMonth(target);
  }

  window.__schedCalendar = { activate };
})();
