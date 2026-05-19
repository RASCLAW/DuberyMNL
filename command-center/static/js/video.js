(function () {
  "use strict";

  var state = { model: "fast", ratio: "1:1", audio: true, startingFrame: null };
  var streaming = false;
  var currentController = null;
  var COST_MAP = { fast: "~$1", full: "~$3-4", lite: "~$0.50-1" };
  var seenVideos = new Set();

  // --- Pill handlers ---
  function initPills(containerId, groupKey) {
    var container = document.getElementById(containerId);
    if (!container) return;
    container.addEventListener("click", function (e) {
      var pill = e.target.closest(".cg-pill");
      if (!pill) return;
      container.querySelectorAll(".cg-pill").forEach(function (p) { p.classList.remove("selected"); });
      pill.classList.add("selected");
      state[groupKey] = pill.dataset.value;
    });
  }

  // --- Audio checkbox ---
  function initAudio() {
    var cb = document.getElementById("vid-audio");
    if (!cb) return;
    cb.addEventListener("change", function () { state.audio = cb.checked; });
  }

  // --- Starting frame (paste or file picker) ---
  function setStartingFrame(file, dataUrl) {
    var ext = (file.type || "image/png").split("/")[1] || "png";
    state.startingFrame = { dataUrl: dataUrl, filename: file.name || ("frame." + ext), type: file.type };
    renderAttachment();
  }

  function clearStartingFrame() {
    state.startingFrame = null;
    renderAttachment();
  }

  function renderAttachment() {
    var wrap = document.getElementById("vid-attachments");
    if (!wrap) return;
    wrap.innerHTML = "";
    if (!state.startingFrame) return;
    var att = document.createElement("div"); att.className = "cg-attachment";
    var img = document.createElement("img"); img.src = state.startingFrame.dataUrl; img.className = "cg-attachment-img";
    var rb = document.createElement("button"); rb.className = "cg-attachment-remove"; rb.textContent = "×";
    rb.title = "Remove starting frame";
    rb.addEventListener("click", clearStartingFrame);
    att.appendChild(img); att.appendChild(rb); wrap.appendChild(att);
  }

  function initPaste() {
    var textarea = document.getElementById("vid-direction");
    if (!textarea) return;
    textarea.addEventListener("paste", function (ev) {
      var items = ev.clipboardData && ev.clipboardData.items;
      if (!items) return;
      for (var i = 0; i < items.length; i++) {
        if (items[i].type.indexOf("image") === 0) {
          ev.preventDefault();
          var file = items[i].getAsFile();
          if (!file) continue;
          var reader = new FileReader();
          reader.onload = (function (f) {
            return function (e) { setStartingFrame(f, e.target.result); };
          })(file);
          reader.readAsDataURL(file);
          break;
        }
      }
    });
  }

  // --- Upload starting frame to server, return path ---
  async function uploadFrame() {
    if (!state.startingFrame) return null;
    var statusEl = document.getElementById("vid-direction-status");
    if (statusEl) statusEl.textContent = "Uploading frame...";
    try {
      var blob = await (await fetch(state.startingFrame.dataUrl)).blob();
      var fd = new FormData();
      fd.append("file", blob, state.startingFrame.filename);
      var res = await fetch("/api/upload-concept", { method: "POST", body: fd });
      var json = await res.json();
      if (statusEl) statusEl.textContent = "";
      return json.path || null;
    } catch (e) {
      if (statusEl) statusEl.textContent = "Upload failed";
      return null;
    }
  }

  // --- Reset agent ---
  function initResetBtn() {
    var btn = document.getElementById("vid-reset-agent");
    if (!btn) return;
    btn.addEventListener("click", function () {
      fetch("/api/agent/reset", { method: "POST" })
        .then(function () { if (window.showToast) showToast("Agent reset", "ok"); })
        .catch(function () { if (window.showToast) showToast("Reset failed", "error"); });
    });
  }

  // --- UI lock/unlock ---
  function lockForm() {
    streaming = true;
    var btn = document.getElementById("vid-generate");
    var reset = document.getElementById("vid-reset-agent");
    var textarea = document.getElementById("vid-direction");
    if (btn) btn.textContent = "Stop";
    if (reset) reset.disabled = true;
    if (textarea) textarea.disabled = true;
  }

  function unlockForm() {
    streaming = false;
    var btn = document.getElementById("vid-generate");
    var reset = document.getElementById("vid-reset-agent");
    var textarea = document.getElementById("vid-direction");
    if (btn) btn.textContent = "Generate";
    if (reset) reset.disabled = false;
    if (textarea) textarea.disabled = false;
  }

  // --- Video bank ---
  function buildVideoCard(item) {
    var card = document.createElement("div");
    card.className = "vid-bank-row";
    card.dataset.url = item.url;
    var meta = [];
    if (item.model) meta.push(item.model);
    if (item.aspect_ratio) meta.push(item.aspect_ratio);
    if (item.size_kb) meta.push(item.size_kb + "KB");
    card.innerHTML =
      '<video class="vid-bank-thumb" src="' + item.url + '" preload="metadata"></video>' +
      '<div class="vid-bank-info">' +
        '<div class="cg-result-filename">' + item.filename + '</div>' +
        (meta.length ? '<div class="cg-result-meta">' + meta.join(" · ") + '</div>' : '') +
        (item.prompt ? '<div class="cg-result-meta" style="font-style:italic;">' + item.prompt.slice(0, 100) + (item.prompt.length > 100 ? "…" : "") + '</div>' : '') +
      '</div>' +
      '<button class="vid-bank-play" title="Play">▶</button>';
    // Toggle play/pause on click
    card.querySelector(".vid-bank-play").addEventListener("click", function () {
      var v = card.querySelector("video");
      if (v.paused) { v.play(); this.textContent = "⏸"; } else { v.pause(); this.textContent = "▶"; }
    });
    return card;
  }

  function loadVideoBank() {
    fetch("/api/video-bank")
      .then(function (r) { return r.json(); })
      .then(function (items) {
        var bank = document.getElementById("vid-bank");
        var empty = document.getElementById("vid-bank-empty");
        var count = document.getElementById("vid-bank-count");
        if (!bank) return;
        // Track which URLs are already rendered
        var existing = new Set();
        bank.querySelectorAll("[data-url]").forEach(function (el) { existing.add(el.dataset.url); });
        var added = 0;
        items.forEach(function (item) {
          if (existing.has(item.url)) return;
          var card = buildVideoCard(item);
          // Prepend so newest is on top
          bank.insertBefore(card, bank.firstChild);
          added++;
        });
        if (empty) empty.style.display = items.length === 0 ? "block" : "none";
        if (count) count.textContent = items.length + " video" + (items.length !== 1 ? "s" : "");
      })
      .catch(function () {});
  }

  function appendVideoToBank(url, filename) {
    var bank = document.getElementById("vid-bank");
    var empty = document.getElementById("vid-bank-empty");
    var count = document.getElementById("vid-bank-count");
    if (!bank) return;
    // Check not already there
    if (bank.querySelector('[data-url="' + url + '"]')) return;
    var card = buildVideoCard({ url: url, filename: filename, prompt: "", model: state.model, aspect_ratio: state.ratio, size_kb: 0 });
    bank.insertBefore(card, bank.firstChild);
    if (empty) empty.style.display = "none";
    var current = bank.querySelectorAll("[data-url]").length;
    if (count) count.textContent = current + " video" + (current !== 1 ? "s" : "");
  }

  // --- Video extraction ---
  function extractVideo(text) {
    // Match relative or absolute paths ending in .mp4 under contents/new/
    var regex = /(?:[A-Za-z]:[\\\/][^\s"'`]*?)?contents[\\/]new[\\/][^\s"'`\)]+\.mp4/gi;
    var match;
    var resultArea = document.getElementById("vid-result-area");
    while ((match = regex.exec(text)) !== null) {
      var rawPath = match[0];
      var normalized = rawPath.replace(/\\/g, "/");
      if (seenVideos.has(normalized)) continue;
      seenVideos.add(normalized);
      var filename = normalized.split("/").pop();
      var apiUrl = "/api/images/" + normalized;
      var card = document.createElement("div");
      card.className = "cg-result-card";
      card.innerHTML =
        '<video controls style="width:100%;border-radius:8px" src="' + apiUrl + '"></video>' +
        '<div class="cg-result-details"><div class="cg-result-filename">' + filename + '</div></div>';
      resultArea.appendChild(card);
      appendVideoToBank(apiUrl, filename);
    }
  }

  // --- Elapsed timer ---
  var _timerInterval = null;

  function startGenStatus(label) {
    var bar = document.getElementById("vid-gen-status");
    var labelEl = document.getElementById("vid-gen-label");
    var elapsedEl = document.getElementById("vid-gen-elapsed");
    if (bar) bar.style.display = "flex";
    if (labelEl) labelEl.textContent = label || "Generating...";
    var start = Date.now();
    clearInterval(_timerInterval);
    _timerInterval = setInterval(function () {
      var s = Math.floor((Date.now() - start) / 1000);
      var m = Math.floor(s / 60);
      if (elapsedEl) elapsedEl.textContent = m + ":" + (s % 60 < 10 ? "0" : "") + (s % 60);
      // Update label hint at key milestones
      if (labelEl) {
        if (s < 15) labelEl.textContent = "Writing Veo prompt...";
        else if (s < 45) labelEl.textContent = "Submitting to Veo...";
        else labelEl.textContent = "Veo is generating your video — this takes 2-5 min";
      }
    }, 1000);
  }

  function stopGenStatus() {
    clearInterval(_timerInterval);
    var bar = document.getElementById("vid-gen-status");
    if (bar) bar.style.display = "none";
    var elapsedEl = document.getElementById("vid-gen-elapsed");
    if (elapsedEl) elapsedEl.textContent = "0:00";
  }

  // --- Chat thread helpers ---
  function addMessage(role, text, imgDataUrl) {
    var msgs = document.getElementById("vid-direction-messages");
    if (!msgs) return null;
    var el = document.createElement("div");
    el.className = "cg-dir-msg cg-dir-" + role;
    if (text) el.textContent = text;
    if (imgDataUrl) {
      var img = document.createElement("img");
      img.src = imgDataUrl;
      img.style.cssText = "max-width:80px;max-height:80px;border-radius:4px;margin-top:4px;display:block;object-fit:cover;";
      el.appendChild(img);
    }
    msgs.appendChild(el);
    msgs.scrollTop = msgs.scrollHeight;
    return el;
  }

  // --- Preset chips ---
  function initPresets() {
    var container = document.getElementById("vid-direction-presets");
    if (!container) return;
    container.addEventListener("click", function (e) {
      var chip = e.target.closest(".cg-preset-chip");
      if (!chip) return;
      var textarea = document.getElementById("vid-direction");
      if (textarea) textarea.value = chip.dataset.preset;
      if (textarea) textarea.focus();
    });
  }

  // --- Ask ---
  function initAskBtn() {
    var btn = document.getElementById("vid-ask");
    var textarea = document.getElementById("vid-direction");
    if (!btn || !textarea) return;
    btn.addEventListener("click", function () { askDirection(); });
    textarea.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); askDirection(); }
    });
  }

  async function askDirection() {
    if (streaming) return;
    var textarea = document.getElementById("vid-direction");
    var statusEl = document.getElementById("vid-direction-status");
    var readyHint = document.getElementById("vid-ready-hint");
    var text = textarea ? textarea.value.trim() : "";
    if (!text && !state.startingFrame) return;

    if (textarea) textarea.value = "";
    if (readyHint) readyHint.style.display = "none";

    // Absorb image into user bubble, then clear the strip (keep state for Generate)
    var absorbedDataUrl = state.startingFrame ? state.startingFrame.dataUrl : null;
    addMessage("user", text || null, absorbedDataUrl);
    if (absorbedDataUrl) {
      var wrap = document.getElementById("vid-attachments");
      if (wrap) wrap.innerHTML = "";
    }

    // Upload frame so agent can Read it
    var framePath = null;
    if (state.startingFrame) {
      framePath = await uploadFrame();
    }

    var prompt =
      "The user is setting up a DuberyMNL video with these settings:\n" +
      "- Model: " + state.model + " (" + COST_MAP[state.model] + ")\n" +
      "- Aspect ratio: " + state.ratio + "\n" +
      "- Audio: " + (state.audio ? "on" : "off") + "\n";
    if (framePath) {
      prompt += "- Starting frame (image-to-video): " + framePath + "\n";
      prompt += "  Read this image file to understand the scene and subject.\n";
    }
    if (text) prompt += "\nTheir direction: \"" + text + "\"\n";
    prompt +=
      "\nAcknowledge the current settings, then state what you understand in 2-3 bullet points. " +
      "If a starting frame is provided, describe what you see in it and how you'd animate it. " +
      "Do NOT ask questions — just confirm your interpretation and say \"Hit Generate when ready.\" " +
      "Fill in any missing details with sensible Veo motion prompt defaults. Do NOT run any tools yet.";

    lockForm();
    if (statusEl) statusEl.textContent = "Thinking...";
    var asstEl = addMessage("assistant", "");
    var got = "";

    try {
      var res = await fetch("/api/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt })
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      var reader = res.body.getReader();
      var decoder = new TextDecoder();
      var buffer = "";
      while (true) {
        var result = await reader.read();
        if (result.done) break;
        buffer += decoder.decode(result.value, { stream: true });
        var parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (var i = 0; i < parts.length; i++) {
          var lines = parts[i].split("\n"), line = null;
          for (var j = 0; j < lines.length; j++) { if (lines[j].startsWith("data:")) { line = lines[j]; break; } }
          if (!line) continue;
          try {
            var obj = JSON.parse(line.slice(5).trim());
            if (obj.text) {
              got += obj.text;
              if (asstEl) { asstEl.textContent = got; document.getElementById("vid-direction-messages").scrollTop = 9999; }
            }
          } catch (e) {}
        }
      }
      if (!got && asstEl) asstEl.textContent = "(no response)";
      if (statusEl) statusEl.textContent = "";
    } catch (e) {
      if (asstEl) asstEl.textContent = "[error] " + e.message;
      if (statusEl) statusEl.textContent = "";
    }

    unlockForm();
  }

  // --- Generate ---
  function initGenerateBtn() {
    var btn = document.getElementById("vid-generate");
    if (!btn) return;

    btn.addEventListener("click", async function () {
      if (streaming) {
        if (currentController) currentController.abort();
        stopGenStatus();
        unlockForm();
        return;
      }

      var direction = (document.getElementById("vid-direction") || {}).value || "";
      direction = direction.trim();
      var hasFrame = !!state.startingFrame;
      if (!direction && !hasFrame) { alert("Enter a direction or paste a starting frame first."); return; }

      if (!confirm("Generate 1 video (" + COST_MAP[state.model] + "). Proceed?")) return;

      // Auto-reset agent
      await fetch("/api/agent/reset", { method: "POST" }).catch(function () {});

      // Upload starting frame if provided
      var startingFramePath = null;
      if (state.startingFrame) {
        startingFramePath = await uploadFrame();
        if (!startingFramePath) { alert("Failed to upload starting frame."); return; }
      }

      // Show workspace
      var progressWrap = document.getElementById("vid-progress-wrap");
      var readyHint = document.getElementById("vid-ready-hint");
      var outputLog = document.getElementById("vid-output-log");
      if (progressWrap) progressWrap.removeAttribute("hidden");
      if (readyHint) readyHint.style.display = "none";
      if (outputLog) outputLog.innerHTML = "";
      seenVideos.clear();
      document.getElementById("vid-result-area").innerHTML = "";
      startGenStatus();

      var timestamp = Date.now();
      // Normalize path separators so the agent doesn't get confused by Windows backslashes
      var normalizedFramePath = startingFramePath ? startingFramePath.replace(/\\/g, "/") : null;
      var prompt =
        "Generate a DuberyMNL video with these settings:\n" +
        "- Model: " + state.model + " (" + COST_MAP[state.model] + ")\n" +
        "- Aspect ratio: " + state.ratio + "\n" +
        "- Audio: " + (state.audio ? "on" : "off") + "\n" +
        (normalizedFramePath ? "- Starting frame path: " + normalizedFramePath + "\n" : "") +
        (direction ? "- Direction: " + direction + "\n" : "") +
        "\nWrite a concise Veo motion prompt based on the direction" +
        (normalizedFramePath ? " and what you see in the starting frame image" : "") +
        ". Focus on camera motion only — not scene description. " +
        "Then run this exact command (copy it as-is, do not modify the paths):\n\n" +
        "python tools/image_gen/generate_videos.py" +
        " --prompt \"<your motion prompt here>\"" +
        " --model " + state.model +
        " --aspect-ratio " + state.ratio +
        (state.audio ? "" : " --no-audio") +
        (normalizedFramePath ? " --image " + normalizedFramePath : "") +
        " --output contents/new/video_" + timestamp + ".mp4\n\n" +
        "Report the full output path when done.";

      lockForm();
      currentController = new AbortController();

      try {
        var res = await fetch("/api/agent/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: prompt }),
          signal: currentController.signal
        });
        var reader = res.body.getReader();
        var decoder = new TextDecoder();
        var buffer = "";
        var got = "";

        while (true) {
          var result = await reader.read();
          if (result.done) break;
          buffer += decoder.decode(result.value, { stream: true });
          var parts = buffer.split("\n\n");
          buffer = parts.pop() || "";
          for (var i = 0; i < parts.length; i++) {
            var lines = parts[i].split("\n"), line = null;
            for (var j = 0; j < lines.length; j++) {
              if (lines[j].startsWith("data:")) { line = lines[j]; break; }
            }
            if (!line) continue;
            try {
              var obj = JSON.parse(line.slice(5).trim());
              if (obj.text) {
                got += obj.text;
                if (outputLog) outputLog.innerHTML = got.replace(/\n/g, "<br>");
              }
              if (obj.done) break;
            } catch (e) {}
          }
          extractVideo(got);
        }
      } catch (e) {
        if (e.name !== "AbortError" && outputLog) {
          outputLog.innerHTML += "<br><em style='color:var(--danger)'>Stream error: " + e.message + "</em>";
        }
      }

      stopGenStatus();
      unlockForm();
    });
  }

  // --- Init ---
  function init() {
    initPills("vid-model-pills", "model");
    initPills("vid-ratio-pills", "ratio");
    initAudio();
    initPaste();
    initPresets();
    initResetBtn();
    initAskBtn();
    initGenerateBtn();
    loadVideoBank();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
