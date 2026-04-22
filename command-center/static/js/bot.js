// Floating bot: click-to-chat overlay + SSE stream from /api/agent/chat.
(function () {
  "use strict";

  const STORAGE_KEY = "command_center_bot_history";
  const MAX_HISTORY = 20;

  const fab = document.getElementById("bot-fab");
  const overlay = document.getElementById("bot-overlay");
  const closeBtn = document.getElementById("bot-close");
  const clearBtn = document.getElementById("bot-clear");
  const messagesEl = document.getElementById("bot-messages");
  const input = document.getElementById("bot-input");
  const sendBtn = document.getElementById("bot-send");

  if (!fab) return; // shell not yet loaded

  // ---------- history ----------
  function loadHistory() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) { return []; }
  }
  function saveHistory(msgs) {
    try {
      const trimmed = msgs.slice(-MAX_HISTORY);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
    } catch (e) {}
  }
  let history = loadHistory();

  function renderHistory() {
    if (!history.length) {
      messagesEl.innerHTML = `<div class="bot-empty">Hey. Ask me anything about DuberyMNL ops, or tell me what to run.</div>`;
      return;
    }
    messagesEl.innerHTML = "";
    for (const m of history) appendBubble(m.role, m.text, false);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }
  function appendBubble(role, text, save = true) {
    const el = document.createElement("div");
    el.className = "bubble " + role;
    el.textContent = text;
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    if (save) {
      history.push({ role, text });
      saveHistory(history);
    }
    return el;
  }
  function clearHistory() {
    history = [];
    saveHistory(history);
    renderHistory();
  }

  // ---------- overlay visibility ----------
  function open() {
    overlay.classList.remove("hidden");
    input.focus();
  }
  function close() { overlay.classList.add("hidden"); }
  fab.addEventListener("click", () => {
    overlay.classList.toggle("hidden");
    if (!overlay.classList.contains("hidden")) input.focus();
  });
  closeBtn.addEventListener("click", close);
  clearBtn.addEventListener("click", () => {
    if (confirm("Clear conversation history?")) clearHistory();
  });

  const isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);

  function parseSseText(raw) {
    let got = "";
    let errMsg = "";
    for (const part of raw.split("\n\n")) {
      const line = part.split("\n").find(l => l.startsWith("data:"));
      if (!line) continue;
      try {
        const obj = JSON.parse(line.slice(5).trim());
        if (obj.text) got += obj.text;
        else if (obj.error) errMsg = obj.error;
      } catch (e) { /* skip malformed */ }
    }
    return { got, errMsg };
  }

  // ---------- SSE send ----------
  async function send() {
    const prompt = input.value.trim();
    if (!prompt || sendBtn.disabled) return;

    appendBubble("user", prompt);
    input.value = "";
    sendBtn.disabled = true;

    const asstEl = appendBubble("assistant", "", false);
    asstEl.classList.add("typing");
    asstEl.textContent = "thinking…";
    let got = "";

    try {
      const res = await fetch("/api/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      if (!res.ok) throw new Error("HTTP " + res.status);

      if (isMobile || !res.body) {
        // Mobile: read full response then parse all SSE events at once
        const raw = await res.text();
        const { got: text, errMsg } = parseSseText(raw);
        asstEl.classList.remove("typing");
        asstEl.textContent = errMsg ? "[error] " + errMsg : (text || "(no response)");
      } else {
        // Desktop: stream chunks as they arrive
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() || "";
          for (const part of parts) {
            const line = part.split("\n").find(l => l.startsWith("data:"));
            if (!line) continue;
            try {
              const obj = JSON.parse(line.slice(5).trim());
              if (obj.text) {
                if (asstEl.classList.contains("typing")) {
                  asstEl.classList.remove("typing");
                  asstEl.textContent = "";
                }
                got += obj.text;
                asstEl.textContent = got;
                messagesEl.scrollTop = messagesEl.scrollHeight;
              } else if (obj.error) {
                asstEl.classList.remove("typing");
                asstEl.textContent = "[error] " + obj.error;
              }
            } catch (e) { /* skip malformed */ }
          }
        }

        if (asstEl.classList.contains("typing")) {
          asstEl.classList.remove("typing");
          asstEl.textContent = "(no response)";
        }
      }

      history.push({ role: "assistant", text: asstEl.textContent });
      saveHistory(history);
    } catch (e) {
      asstEl.classList.remove("typing");
      asstEl.textContent = "[fetch error] " + e.message;
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  sendBtn.addEventListener("click", send);
  input.addEventListener("keydown", ev => {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      send();
    }
  });

  // auto-grow textarea up to 80px (matches CSS max-height)
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 80) + "px";
  });

  // initial paint
  renderHistory();
})();
