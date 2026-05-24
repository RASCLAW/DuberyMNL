// Schedule -> AI Suggest tab. Image-aware chat with Claude (vision via Read tool).
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const SESSION_KEY = "cc.schedule.chat.session_id";

  const state = {
    sessionId: null,
    inFlight: false,
    wired: false,
  };

  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  }

  function toast(msg, kind) {
    if (window.__toast) window.__toast(msg, kind);
    else console.log("[schedChat]", msg);
  }

  function uuid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return "sched-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
  }

  function ensureSessionId() {
    if (state.sessionId) return state.sessionId;
    let sid = "";
    try { sid = localStorage.getItem(SESSION_KEY) || ""; } catch (e) {}
    if (!sid) {
      sid = "sched-" + uuid();
      try { localStorage.setItem(SESSION_KEY, sid); } catch (e) {}
    }
    state.sessionId = sid;
    return sid;
  }

  function getComposerImages() {
    // schedule.js owns the composer state; surface its images for thumb display.
    if (window.__schedState && Array.isArray(window.__schedState.images)) return window.__schedState.images;
    return [];
  }

  function renderThumbs() {
    const wrap = $("schedChatThumbs");
    const empty = $("schedChatThumbsEmpty");
    if (!wrap) return;
    const imgs = getComposerImages();
    console.log("[schedChat] renderThumbs:", imgs.length, "images,", "bridge=", !!window.__schedState);
    // Clear existing thumbs (keep the empty placeholder element if present)
    Array.from(wrap.querySelectorAll("img,div.sched-chat-thumb-wrap")).forEach(n => n.remove());
    if (!imgs.length) {
      if (empty) empty.style.display = "";
      return;
    }
    if (empty) empty.style.display = "none";
    const frag = document.createDocumentFragment();
    imgs.forEach(img => {
      const im = document.createElement("img");
      im.src = img.src_url;
      im.alt = img.filename || "";
      im.title = img.filename || "";
      im.loading = "lazy";
      frag.appendChild(im);
    });
    wrap.appendChild(frag);
  }

  // Parse "OPTION N -- label" blocks out of assistant text into structured option cards.
  function parseOptionBlocks(text) {
    const lines = text.split(/\r?\n/);
    const out = [];
    let cur = null;
    let preamble = [];
    let sawOption = false;
    lines.forEach(line => {
      const m = line.match(/^\s*(OPTION\s+\d+|REVISED|FINAL)\s*[-:]+\s*(.*)$/i);
      if (m) {
        if (cur) out.push(cur);
        cur = { label: m[1].toUpperCase() + (m[2] ? " -- " + m[2] : ""), lines: [] };
        sawOption = true;
      } else if (cur) {
        cur.lines.push(line);
      } else {
        preamble.push(line);
      }
    });
    if (cur) out.push(cur);
    return { preamble: preamble.join("\n").trim(), options: out, hasOptions: sawOption };
  }

  function renderMessage(role, content, opts) {
    const list = $("schedChatMessages");
    if (!list) return null;
    const ph = $("schedChatPlaceholder");
    if (ph) ph.remove();
    const wrap = document.createElement("div");
    wrap.className = `sched-chat-msg ${role}`;
    const bubble = document.createElement("div");
    bubble.className = `sched-chat-bubble ${role}`;
    if (opts && opts.error) bubble.classList.add("error");
    if (opts && opts.thinking) bubble.classList.add("thinking");

    if (role === "assistant" && content && !(opts && opts.thinking) && !(opts && opts.error)) {
      const parsed = parseOptionBlocks(content);
      if (parsed.hasOptions) {
        if (parsed.preamble) {
          const pre = document.createElement("div");
          pre.textContent = parsed.preamble;
          pre.style.marginBottom = "6px";
          bubble.appendChild(pre);
        }
        parsed.options.forEach(opt => {
          const card = document.createElement("div");
          card.className = "sched-chat-option";
          const lbl = document.createElement("div");
          lbl.className = "sched-chat-option-label";
          lbl.textContent = opt.label;
          const body = document.createElement("div");
          body.className = "sched-chat-option-body";
          body.textContent = opt.lines.join("\n").trim();
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "sched-chat-copy";
          btn.textContent = "Copy";
          btn.addEventListener("click", () => {
            const txt = body.textContent;
            navigator.clipboard.writeText(txt).then(() => {
              btn.textContent = "Copied";
              btn.classList.add("copied");
              setTimeout(() => { btn.textContent = "Copy"; btn.classList.remove("copied"); }, 1500);
            }).catch(() => toast("Copy failed", "bad"));
          });
          card.appendChild(lbl);
          card.appendChild(body);
          card.appendChild(btn);
          bubble.appendChild(card);
        });
      } else {
        bubble.textContent = content;
      }
    } else {
      bubble.textContent = content || "";
    }
    wrap.appendChild(bubble);
    list.appendChild(wrap);
    list.scrollTop = list.scrollHeight;
    return wrap;
  }

  function clearMessages() {
    const list = $("schedChatMessages");
    if (!list) return;
    list.innerHTML = `<div class="sched-chat-placeholder" id="schedChatPlaceholder">Pick a Quick Ask or type below to start.</div>`;
  }

  function updateMeta(count, tokens) {
    const el = $("schedChatMeta");
    if (!el) return;
    const t = (typeof tokens === "number") ? ` &middot; ~${(tokens / 1000).toFixed(1)}K tokens` : "";
    el.innerHTML = `${count || 0} message${count === 1 ? "" : "s"}${t}`;
  }

  async function loadHistory() {
    const sid = ensureSessionId();
    try {
      const r = await fetch(`/api/schedule/chat/history?session_id=${encodeURIComponent(sid)}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      clearMessages();
      (data.messages || []).forEach(m => renderMessage(m.role, m.content, { error: !!m.error }));
      updateMeta(data.messages ? data.messages.length : 0, data.token_estimate);
    } catch (e) {
      console.error("chat history failed", e);
    }
  }

  async function sendMessage(text) {
    if (state.inFlight) return;
    if (!text || !text.trim()) return;
    state.inFlight = true;
    const askBtn = $("schedChatAsk");
    const input = $("schedChatInput");
    if (askBtn) askBtn.disabled = true;
    if (input) input.disabled = true;

    const sid = ensureSessionId();
    const imgs = getComposerImages();
    const image_paths = imgs.map(i => i.path);

    renderMessage("user", text);
    const thinkingEl = renderMessage("assistant", "Claude is thinking", { thinking: true });

    try {
      const r = await fetch("/api/schedule/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sid, message: text, image_paths }),
      });
      const data = await r.json();
      if (thinkingEl) thinkingEl.remove();
      if (!data.ok) {
        renderMessage("assistant", data.error || `HTTP ${r.status}`, { error: true });
        toast(data.error || `Chat failed (${r.status})`, "bad");
      } else {
        renderMessage("assistant", data.message.content);
        updateMeta(data.message_count, data.token_estimate);
      }
    } catch (e) {
      if (thinkingEl) thinkingEl.remove();
      renderMessage("assistant", `Network error: ${e.message}`, { error: true });
      toast("Network error: " + e.message, "bad");
    } finally {
      state.inFlight = false;
      if (askBtn) askBtn.disabled = false;
      if (input) { input.disabled = false; input.value = ""; input.focus(); autosize(input); }
    }
  }

  function autosize(ta) {
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(140, ta.scrollHeight) + "px";
  }

  async function resetThread() {
    if (!confirm("Reset this chat thread? Claude will start fresh.")) return;
    const sid = ensureSessionId();
    try {
      const r = await fetch("/api/schedule/chat/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sid }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      // Rotate session_id so server starts a fresh Claude resume too
      try { localStorage.removeItem(SESSION_KEY); } catch (e) {}
      state.sessionId = null;
      ensureSessionId();
      clearMessages();
      updateMeta(0, 0);
      toast("Thread reset", "ok");
    } catch (e) {
      toast("Reset failed: " + e.message, "bad");
    }
  }

  function wire() {
    if (state.wired) return;
    state.wired = true;

    // React to composer image changes in real-time (works even if AI Suggest panel is currently visible)
    document.addEventListener("sched:images-changed", () => renderThumbs());

    const input = $("schedChatInput");
    if (input) {
      input.addEventListener("input", () => autosize(input));
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          const v = input.value.trim();
          if (v) sendMessage(v);
        }
      });
    }

    const form = $("schedChatForm");
    if (form) form.addEventListener("submit", (e) => {
      e.preventDefault();
      const v = (input && input.value.trim()) || "";
      if (v) sendMessage(v);
    });

    const ask = $("schedChatAsk");
    if (ask) ask.addEventListener("click", (e) => {
      e.preventDefault();
      const v = (input && input.value.trim()) || "";
      if (v) sendMessage(v);
    });

    // Preset chips: drop text into composer, focus, but DO NOT auto-send (RA can edit first)
    document.querySelectorAll("#schedChatPresets .sched-chat-preset").forEach(btn => {
      btn.addEventListener("click", () => {
        if (!input) return;
        input.value = btn.dataset.preset || "";
        autosize(input);
        input.focus();
        // Move cursor to end
        const len = input.value.length;
        input.setSelectionRange(len, len);
      });
    });

    const reset = $("schedChatReset");
    if (reset) reset.addEventListener("click", resetThread);

    // Emoji picker -- curated set for DuberyMNL captions. Click inserts at the
    // current cursor position in the chat input; clicking the button toggles;
    // clicking outside closes.
    const emojiBtn = $("schedChatEmojiBtn");
    const emojiPicker = $("schedEmojiPicker");
    if (emojiBtn && emojiPicker && input) {
      const EMOJI_GROUPS = [
        { label: "Shades & vibe", items: ["🕶️", "😎", "✨", "⚡", "🔥", "💯", "💎", "🌟"] },
        { label: "Outdoor & light", items: ["☀️", "🌅", "🌇", "🌴", "🌊", "🏖️", "🏞️", "🌄"] },
        { label: "Action & game", items: ["🎮", "🕹️", "🎯", "🏆", "🥇", "💪", "👀", "🙌"] },
        { label: "Shop & ship", items: ["🛒", "🛍️", "📦", "🚚", "💸", "💰", "🔔", "📲"] },
        { label: "Reactions", items: ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤝", "🎉"] },
      ];
      const groupsHtml = EMOJI_GROUPS.map(g => {
        const row = g.items.map(e => `<button type="button" data-emoji="${e}" title="${e}">${e}</button>`).join("");
        return `<div class="emoji-row-label">${g.label}</div>${row}`;
      }).join("");
      emojiPicker.innerHTML = groupsHtml;

      const closePicker = () => { emojiPicker.hidden = true; };
      const openPicker = () => { emojiPicker.hidden = false; };

      emojiBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (emojiPicker.hidden) openPicker(); else closePicker();
      });
      emojiPicker.addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-emoji]");
        if (!btn) return;
        const emoji = btn.dataset.emoji || "";
        const start = input.selectionStart ?? input.value.length;
        const end = input.selectionEnd ?? input.value.length;
        input.value = input.value.slice(0, start) + emoji + input.value.slice(end);
        const newPos = start + emoji.length;
        input.focus();
        input.setSelectionRange(newPos, newPos);
        autosize(input);
      });
      // Click outside the picker (and not on the toggle button) closes it.
      document.addEventListener("click", (e) => {
        if (emojiPicker.hidden) return;
        if (emojiPicker.contains(e.target) || emojiBtn.contains(e.target)) return;
        closePicker();
      });
      // Esc closes
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !emojiPicker.hidden) closePicker();
      });
    }
  }

  function activate() {
    wire();
    ensureSessionId();
    renderThumbs();
    loadHistory();
    // Refresh thumbs each time tab opens (composer may have changed)
  }

  window.__schedChat = { activate };
})();
