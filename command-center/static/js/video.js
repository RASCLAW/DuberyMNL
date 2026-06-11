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

  // --- Video bank -----------------------------------------------------------
  // Interim upgrade of the in-tab Videos list (the full Video Bank tab needs a
  // server restart). Compressed poster thumbnails (pre-generated JPGs served by
  // /api/images), newest-first, a modal player with prev/next, and favorites
  // persisted via the existing /api/schedule/favorites endpoint.

  var bankItems = [];        // all clips, newest-first (from /api/video-bank)
  var renderedItems = [];    // the subset currently shown (honors favOnly)
  var favorites = new Set(); // favorited URLs
  var favOnly = false;

  function urlToPath(url) { return (url || "").replace(/^\/api\/images\//, ""); }
  function pathToUrl(p) { return "/api/images/" + p; }

  // Poster URL for a clip -- on-the-fly compressed JPG from the live endpoint
  // (app.py /api/video-thumb): generated on demand + cached by source mtime, so
  // it never goes stale (unlike the old pre-baked .tmp/video_posters/ stopgap).
  // w=180 ~= 2x the 80x56 display size (snaps to the nearest allowed width).
  function posterUrl(videoUrl) {
    var rel = urlToPath(videoUrl);
    var enc = rel.split("/").map(encodeURIComponent).join("/");
    return "/api/video-thumb/" + enc + "?w=180";
  }

  function loadFavorites() {
    return fetch("/api/schedule/favorites")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var paths = (d && Array.isArray(d.favorites)) ? d.favorites : [];
        favorites = new Set(paths.map(pathToUrl));
      })
      .catch(function () { favorites = new Set(); });
  }

  function toggleFavorite(url) {
    var willFav = !favorites.has(url);
    if (willFav) favorites.add(url); else favorites.delete(url);
    fetch("/api/schedule/favorites", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: urlToPath(url), action: "toggle" }),
    }).catch(function () { if (willFav) favorites.delete(url); else favorites.add(url); });
  }

  function buildVideoCard(item, idx) {
    var card = document.createElement("div");
    card.className = "vid-bank-row";
    card.dataset.url = item.url;
    var meta = [];
    if (item.model) meta.push(item.model);
    if (item.aspect_ratio) meta.push(item.aspect_ratio);
    if (item.size_kb) meta.push(item.size_kb + "KB");

    var wrap = document.createElement("div");
    wrap.className = "vidx-thumb-wrap";
    var img = document.createElement("img");
    img.className = "vid-bank-thumb";
    img.loading = "lazy";
    img.decoding = "async";
    img.alt = item.filename;
    img.src = posterUrl(item.url);
    // Missing poster (e.g. a freshly generated clip) -> inline first-frame video.
    img.addEventListener("error", function once() {
      img.removeEventListener("error", once);
      var v = document.createElement("video");
      v.className = "vid-bank-thumb";
      v.preload = "metadata";
      v.muted = true;
      v.playsInline = true;
      v.src = item.url + "#t=0.1";
      if (img.parentNode) img.parentNode.replaceChild(v, img);
    }, { once: true });
    var badge = document.createElement("span");
    badge.className = "vidx-play-badge";
    var heart = document.createElement("button");
    heart.className = "vidx-heart" + (favorites.has(item.url) ? " faved" : "");
    heart.textContent = favorites.has(item.url) ? "♥" : "♡";
    heart.title = favorites.has(item.url) ? "Remove from favorites" : "Add to favorites";
    heart.addEventListener("click", function (e) {
      e.stopPropagation();
      toggleFavorite(item.url);
      var f = favorites.has(item.url);
      heart.classList.toggle("faved", f);
      heart.textContent = f ? "♥" : "♡";
      heart.title = f ? "Remove from favorites" : "Add to favorites";
      if (favOnly && !f) renderBank();   // it just left the favorites filter
    });
    wrap.appendChild(img);
    wrap.appendChild(badge);
    wrap.appendChild(heart);

    var info = document.createElement("div");
    info.className = "vid-bank-info";
    info.innerHTML =
      '<div class="cg-result-filename">' + item.filename + '</div>' +
      (meta.length ? '<div class="cg-result-meta">' + meta.join(" · ") + '</div>' : '') +
      (item.prompt ? '<div class="cg-result-meta" style="font-style:italic;">' + item.prompt.slice(0, 100) + (item.prompt.length > 100 ? "…" : "") + '</div>' : '');

    card.appendChild(wrap);
    card.appendChild(info);
    card.addEventListener("click", function () { openModal(idx); });
    return card;
  }

  function renderBank() {
    var bank = document.getElementById("vid-bank");
    var empty = document.getElementById("vid-bank-empty");
    var count = document.getElementById("vid-bank-count");
    if (!bank) return;
    renderedItems = favOnly ? bankItems.filter(function (it) { return favorites.has(it.url); }) : bankItems;
    // Clear existing cards (keep the persistent empty-state node).
    bank.querySelectorAll(".vid-bank-row").forEach(function (el) { el.remove(); });
    renderedItems.forEach(function (item, idx) {
      bank.appendChild(buildVideoCard(item, idx));   // already newest-first
    });
    if (empty) {
      empty.style.display = renderedItems.length === 0 ? "block" : "none";
      empty.textContent = favOnly ? "No favorites yet — tap ♡ on a clip." : "No videos yet";
    }
    if (count) count.textContent = renderedItems.length + " video" + (renderedItems.length !== 1 ? "s" : "");
  }

  function loadVideoBank() {
    Promise.all([
      fetch("/api/video-bank").then(function (r) { return r.json(); }).catch(function () { return []; }),
      loadFavorites(),
    ]).then(function (res) {
      bankItems = Array.isArray(res[0]) ? res[0] : [];   // API returns newest-first
      bankItems.forEach(function (it) { seenVideos.add(urlToPath(it.url)); });
      renderBank();
    });
  }

  function appendVideoToBank(url, filename) {
    if (bankItems.some(function (it) { return it.url === url; })) return;
    bankItems.unshift({ url: url, filename: filename, prompt: "", model: state.model, aspect_ratio: state.ratio, size_kb: 0 });
    renderBank();
  }

  // --- Modal player (pop-up, not fullscreen) ---------------------------------

  var modalEl = null;

  function ensureModal() {
    if (modalEl) return modalEl;
    injectBankStyles();
    var m = document.createElement("div");
    m.className = "vidx-modal hidden";
    m.innerHTML =
      '<div class="vidx-backdrop"></div>' +
      '<div class="vidx-box">' +
        '<button class="vidx-close" title="Close">×</button>' +
        '<button class="vidx-arrow vidx-prev" title="Previous">‹</button>' +
        '<button class="vidx-arrow vidx-next" title="Next">›</button>' +
        '<video class="vidx-video" controls playsinline webkit-playsinline preload="metadata"></video>' +
        '<div class="vidx-meta">' +
          '<span class="vidx-pos"></span>' +
          '<span class="vidx-name"></span>' +
          '<a class="vidx-dl btn" download>Download</a>' +
          '<button class="vidx-fav btn">♥ Favorite</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(m);
    m.querySelector(".vidx-close").addEventListener("click", closeModal);
    m.querySelector(".vidx-backdrop").addEventListener("click", closeModal);
    m.querySelector(".vidx-prev").addEventListener("click", function () { modalNav(-1); });
    m.querySelector(".vidx-next").addEventListener("click", function () { modalNav(1); });
    m.querySelector(".vidx-fav").addEventListener("click", function () {
      var item = renderedItems[modalIndex];
      if (!item) return;
      toggleFavorite(item.url);
      syncModalFav();
      // Reflect on the matching card heart.
      var card = document.querySelector('#vid-bank .vid-bank-row[data-url="' + (window.CSS && CSS.escape ? CSS.escape(item.url) : item.url) + '"] .vidx-heart');
      if (card) {
        var f = favorites.has(item.url);
        card.classList.toggle("faved", f);
        card.textContent = f ? "♥" : "♡";
      }
    });
    modalEl = m;
    return m;
  }

  var modalIndex = 0;

  function openModal(idx) {
    ensureModal();
    modalIndex = idx;
    updateModal();
    modalEl.classList.remove("hidden");
  }

  function updateModal() {
    var item = renderedItems[modalIndex];
    if (!item) return;
    var v = modalEl.querySelector(".vidx-video");
    v.pause();
    v.src = item.url;
    v.load();
    modalEl.querySelector(".vidx-name").textContent = item.filename;
    modalEl.querySelector(".vidx-pos").textContent = (modalIndex + 1) + " / " + renderedItems.length;
    var dl = modalEl.querySelector(".vidx-dl");
    dl.href = item.url; dl.download = item.filename;
    modalEl.querySelector(".vidx-prev").disabled = modalIndex === 0;
    modalEl.querySelector(".vidx-next").disabled = modalIndex === renderedItems.length - 1;
    syncModalFav();
  }

  function syncModalFav() {
    var item = renderedItems[modalIndex];
    if (!item) return;
    var btn = modalEl.querySelector(".vidx-fav");
    var f = favorites.has(item.url);
    btn.textContent = f ? "♥ Unfavorite" : "♡ Favorite";
    btn.classList.toggle("faved", f);
  }

  function modalNav(d) {
    var n = modalIndex + d;
    if (n < 0 || n >= renderedItems.length) return;
    modalIndex = n;
    updateModal();
  }

  function closeModal() {
    if (!modalEl) return;
    var v = modalEl.querySelector(".vidx-video");
    v.pause();
    v.removeAttribute("src");
    v.load();
    modalEl.classList.add("hidden");
  }

  document.addEventListener("keydown", function (e) {
    if (!modalEl || modalEl.classList.contains("hidden")) return;
    if (e.key === "Escape") closeModal();
    else if (e.key === "ArrowLeft") modalNav(-1);
    else if (e.key === "ArrowRight") modalNav(1);
  });

  // --- Bank UI: favorites filter toggle + styles -----------------------------

  function initVideoBankUI() {
    injectBankStyles();
    ensureModal();
    var countEl = document.getElementById("vid-bank-count");
    if (countEl && countEl.parentNode && !document.getElementById("vid-fav-only")) {
      var toggle = document.createElement("button");
      toggle.id = "vid-fav-only";
      toggle.className = "vidx-favfilter";
      toggle.textContent = "♥ Only";
      toggle.title = "Show favorites only";
      toggle.addEventListener("click", function () {
        favOnly = !favOnly;
        toggle.classList.toggle("on", favOnly);
        renderBank();
      });
      countEl.parentNode.insertBefore(toggle, countEl);
    }
  }

  function injectBankStyles() {
    if (document.getElementById("vidx-styles")) return;
    var css =
      ".vidx-thumb-wrap{position:relative;flex:0 0 auto;}" +
      ".vidx-thumb-wrap .vid-bank-thumb{display:block;object-fit:cover;cursor:pointer;}" +
      ".vidx-play-badge{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:30px;height:30px;border-radius:50%;background:rgba(15,17,21,.55);border:1.5px solid rgba(255,255,255,.85);pointer-events:none;}" +
      ".vidx-play-badge::before{content:'';position:absolute;top:50%;left:53%;transform:translate(-50%,-50%);border-style:solid;border-width:6px 0 6px 10px;border-color:transparent transparent transparent #fff;}" +
      ".vidx-heart{position:absolute;top:4px;left:4px;width:24px;height:24px;border:none;border-radius:50%;background:rgba(0,0,0,.45);color:#fff;font-size:14px;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;}" +
      ".vidx-heart.faved{color:#ff5a7a;}" +
      ".vid-bank-row{cursor:pointer;}" +
      ".vidx-favfilter{font-size:11px;padding:3px 9px;margin-right:8px;border-radius:999px;border:1px solid var(--border);background:var(--surface-2,transparent);color:var(--text-muted,#aaa);cursor:pointer;}" +
      ".vidx-favfilter.on{border-color:#ff5a7a;color:#ff5a7a;}" +
      ".vidx-modal{position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;}" +
      ".vidx-modal.hidden{display:none;}" +
      ".vidx-backdrop{position:absolute;inset:0;background:rgba(0,0,0,.78);}" +
      ".vidx-box{position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;gap:10px;max-width:94vw;}" +
      ".vidx-video{display:block;max-width:92vw;max-height:78vh;width:auto;background:#000;border-radius:8px;}" +
      ".vidx-close{position:absolute;top:-38px;right:0;width:32px;height:32px;border:none;border-radius:50%;background:rgba(255,255,255,.12);color:#fff;font-size:20px;cursor:pointer;}" +
      ".vidx-arrow{position:absolute;top:50%;transform:translateY(-50%);width:42px;height:42px;border:none;border-radius:50%;background:rgba(255,255,255,.14);color:#fff;font-size:26px;cursor:pointer;z-index:2;}" +
      ".vidx-arrow:disabled{opacity:.25;cursor:default;}" +
      ".vidx-prev{left:-54px;}.vidx-next{right:-54px;}" +
      "@media(max-width:720px){.vidx-prev{left:4px;}.vidx-next{right:4px;background:rgba(0,0,0,.4);}.vidx-prev{background:rgba(0,0,0,.4);}}" +
      ".vidx-meta{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:center;color:#ddd;font-size:13px;max-width:92vw;}" +
      ".vidx-fav.faved{color:#ff5a7a;border-color:#ff5a7a;}";
    var st = document.createElement("style");
    st.id = "vidx-styles";
    st.textContent = css;
    document.head.appendChild(st);
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
    initVideoBankUI();
    loadVideoBank();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
