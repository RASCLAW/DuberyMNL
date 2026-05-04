// Content Gen tab: two-column layout.
// Left: form (mode/type/count/products) + direction chat + generate.
// Right: unified workspace -- progress log + image result cards + feedback + history.
(function () {
  "use strict";

  // --- state ---
  var state = { mode: "ugc", type: "person", count: 1, ratio: "1:1", products: [] };
  var streaming = false;
  var currentController = null;
  var allProducts = [];
  var MAX_PRODUCTS = 4;
  var conceptImages = [];
  var pendingConcepts = []; // concepts moved to output during generation

  // --- DOM refs ---
  var thinkingStatus = document.getElementById("cg-thinking-status");
  var outputBody = document.getElementById("cg-output-body");
  var historyArea = document.getElementById("cg-history-area");
  var imageCount = document.getElementById("cg-image-count");
  var inputEl = document.getElementById("cg-input");
  var directionEl = document.getElementById("cg-direction");
  var directionMessages = document.getElementById("cg-direction-messages");
  var directionAttachments = document.getElementById("cg-direction-attachments");
  var directionStatus = document.getElementById("cg-direction-status");
  var directionSendBtn = document.getElementById("cg-direction-send");
  var sendBtn = document.getElementById("cg-send");
  var genBtn = document.getElementById("cg-generate");
  var clearBtn = document.getElementById("cg-clear");
  var resetAgentBtn = document.getElementById("cg-reset-agent");
  var countEl = document.getElementById("cg-count");
  var minusBtn = document.getElementById("cg-minus");
  var plusBtn = document.getElementById("cg-plus");
  var productList = document.getElementById("cg-product-list");
  var addProductBtn = document.getElementById("cg-add-product");

  if (!genBtn) return;

  // --- stats refs ---
  var statsToggle = document.getElementById("cg-stats-toggle");
  var statsBody = document.getElementById("cg-stats-body");
  var statsTotal = document.getElementById("cg-stats-total");
  var statsTbody = document.getElementById("cg-stats-tbody");
  var statsTfoot = document.getElementById("cg-stats-tfoot");

  // =========================================================
  // PRODUCTS
  // =========================================================
  async function loadProducts() {
    try { var res = await fetch("/api/products"); allProducts = await res.json(); }
    catch (e) { allProducts = []; }
    renderProductSlots();
    loadStats();
  }

  function prettyName(key) {
    return key.split("-").map(function (w) { return w.charAt(0).toUpperCase() + w.slice(1); }).join(" ");
  }

  function renderProductSlots() {
    productList.innerHTML = "";
    if (state.products.length === 0) {
      productList.appendChild(createProductDropdown(0, ""));
      addProductBtn.classList.add("hidden");
      return;
    }
    for (var i = 0; i < state.products.length; i++) productList.appendChild(createProductDropdown(i, state.products[i]));
    addProductBtn.classList[state.products.length > 0 && state.products.length < MAX_PRODUCTS ? "remove" : "add"]("hidden");
  }

  function createProductDropdown(index, selected) {
    var wrap = document.createElement("div"); wrap.className = "cg-product-row";
    var sel = document.createElement("select"); sel.className = "cg-product-select"; sel.dataset.index = index;
    var opt0 = document.createElement("option"); opt0.value = ""; opt0.textContent = "Random"; sel.appendChild(opt0);
    for (var i = 0; i < allProducts.length; i++) {
      var opt = document.createElement("option"); opt.value = allProducts[i]; opt.textContent = prettyName(allProducts[i]);
      if (allProducts[i] === selected) opt.selected = true; sel.appendChild(opt);
    }
    sel.addEventListener("change", function () {
      var idx = parseInt(this.dataset.index);
      if (this.value) { state.products[idx] = this.value; } else {
        if (state.products.length > 1) state.products.splice(idx, 1); else state.products = [];
      }
      renderProductSlots(); updateReadyHint();
    });
    wrap.appendChild(sel);
    if (state.products.length > 0 && (state.products.length > 1 || selected)) {
      var rb = document.createElement("button"); rb.className = "btn cg-product-remove"; rb.textContent = "\u00D7";
      rb.dataset.index = index;
      rb.addEventListener("click", function () { state.products.splice(parseInt(this.dataset.index), 1); renderProductSlots(); updateReadyHint(); });
      wrap.appendChild(rb);
    }
    return wrap;
  }

  addProductBtn.addEventListener("click", function () {
    if (streaming || state.products.length >= MAX_PRODUCTS) return;
    state.products.push(""); renderProductSlots();
  });

  // =========================================================
  // STATS
  // =========================================================
  async function loadStats() {
    try { var res = await fetch("/api/content-stats"); renderStats(await res.json()); } catch (e) {}
  }

  function renderStats(data) {
    statsTotal.textContent = data.totals.all + " images";
    statsTbody.innerHTML = "";
    var keys = Object.keys(data.products).sort();
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i], p = data.products[k], ugc = p.person + p.product;
      var tr = document.createElement("tr");
      tr.innerHTML = "<td>" + prettyName(k) + "</td><td" + (p.person === 0 ? ' class="cg-stats-zero"' : "") + ">" + p.person + "</td><td" + (p.product === 0 ? ' class="cg-stats-zero"' : "") + ">" + p.product + "</td><td><strong>" + ugc + "</strong></td>";
      statsTbody.appendChild(tr);
    }
    var totalUgc = data.totals.person + data.totals.product;
    statsTfoot.innerHTML = "<tr><td>UGC</td><td>" + data.totals.person + "</td><td>" + data.totals.product + "</td><td><strong>" + totalUgc + "</strong></td></tr><tr><td>Brand</td><td colspan='3' style='text-align:center'>" + data.brand + "</td></tr><tr><td>Total</td><td colspan='3' style='text-align:center'><strong>" + data.totals.all + "</strong></td></tr>";
  }

  if (statsToggle) statsToggle.addEventListener("click", function () { statsBody.classList.toggle("hidden"); });

  // =========================================================
  // READY HINT + HISTORY TOGGLE
  // =========================================================
  var readySummary = document.getElementById("cg-ready-summary");
  var historyToggle = document.getElementById("cg-history-toggle");
  var historyCount = document.getElementById("cg-history-count");

  function updateReadyHint() {
    if (!readySummary) return;
    var products = state.products.filter(function (p) { return p; });
    var productText = products.length ? products.map(prettyName).join(", ") : "random product";
    var modeLabel = state.mode === "bespoke" ? "Bespoke concept" : state.mode.toUpperCase() + " " + state.type.charAt(0).toUpperCase() + state.type.slice(1);
    readySummary.textContent = state.count + " " + modeLabel + " shot" + (state.count > 1 ? "s" : "") + " (" + state.ratio + "), " + productText;
  }

  if (historyToggle) historyToggle.addEventListener("click", function () { historyArea.classList.toggle("hidden"); });

  // =========================================================
  // PILLS + STEPPER
  // =========================================================
  document.querySelectorAll(".cg-pills").forEach(function (row) {
    row.addEventListener("click", function (ev) {
      var pill = ev.target.closest(".cg-pill");
      if (!pill || streaming) return;
      row.querySelectorAll(".cg-pill").forEach(function (p) { p.classList.remove("selected"); });
      pill.classList.add("selected");
      state[row.dataset.field] = pill.dataset.value;
      updateReadyHint();
    });
  });

  minusBtn.addEventListener("click", function () { if (streaming) return; state.count = Math.max(1, state.count - 1); countEl.textContent = state.count; updateReadyHint(); });
  plusBtn.addEventListener("click", function () { if (streaming) return; state.count = Math.min(10, state.count + 1); countEl.textContent = state.count; updateReadyHint(); });

  // =========================================================
  // DIRECTION MINI-CHAT
  // =========================================================
  var attachBtn  = document.getElementById("cg-attach-btn");
  var conceptFileInput = document.getElementById("cg-concept-file");
  attachBtn.addEventListener("click", function () { conceptFileInput.click(); });
  conceptFileInput.addEventListener("change", function () {
    if (this.files && this.files[0]) { uploadConceptImage(this.files[0]); this.value = ""; }
  });

  directionEl.addEventListener("paste", function (ev) {
    var items = ev.clipboardData && ev.clipboardData.items;
    if (!items) return;
    for (var i = 0; i < items.length; i++) {
      if (items[i].type.indexOf("image") === 0) {
        ev.preventDefault(); uploadConceptImage(items[i].getAsFile()); return;
      }
    }
  });
  directionEl.addEventListener("dragover", function (ev) { ev.preventDefault(); });
  directionEl.addEventListener("drop", function (ev) {
    ev.preventDefault();
    var files = ev.dataTransfer && ev.dataTransfer.files;
    if (files) for (var i = 0; i < files.length; i++) { if (files[i].type.indexOf("image") === 0) { uploadConceptImage(files[i]); return; } }
  });

  async function uploadConceptImage(file) {
    directionStatus.textContent = "Uploading...";
    var reader = new FileReader();
    reader.onload = async function (e) {
      var dataUrl = e.target.result;
      try {
        var res = await fetch("/api/upload-concept", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ image_data: dataUrl, ext: file.type.split("/")[1] || "png" }) });
        var data = await res.json();
        if (data.ok) { conceptImages.push({ path: data.path, filename: data.filename, dataUrl: dataUrl }); renderAttachments(); directionStatus.textContent = ""; }
        else directionStatus.textContent = "Upload failed";
      } catch (err) { directionStatus.textContent = "Upload error"; }
    };
    reader.readAsDataURL(file);
  }

  function renderAttachments() {
    directionAttachments.innerHTML = "";
    for (var i = 0; i < conceptImages.length; i++) {
      var att = conceptImages[i], wrap = document.createElement("div"); wrap.className = "cg-attachment";
      var img = document.createElement("img"); img.src = att.dataUrl; img.className = "cg-attachment-img";
      var rb = document.createElement("button"); rb.className = "cg-attachment-remove"; rb.textContent = "\u00D7"; rb.dataset.index = i;
      rb.addEventListener("click", function () { conceptImages.splice(parseInt(this.dataset.index), 1); renderAttachments(); });
      wrap.appendChild(img); wrap.appendChild(rb); directionAttachments.appendChild(wrap);
    }
  }

  function addDirectionMessage(role, text) {
    var el = document.createElement("div"); el.className = "cg-dir-msg cg-dir-" + role; el.textContent = text;
    directionMessages.appendChild(el); directionMessages.scrollTop = directionMessages.scrollHeight; return el;
  }

  // Preset chips: insert into direction input on click (don't auto-send).
  document.querySelectorAll(".cg-preset-chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      if (streaming) return;
      var text = this.dataset.preset || "";
      directionEl.value = directionEl.value ? directionEl.value.trim() + " " + text : text;
      directionEl.focus();
    });
  });

  directionSendBtn.addEventListener("click", function () { askDirection(); });
  directionEl.addEventListener("keydown", function (ev) { if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); askDirection(); } });

  async function askDirection() {
    var text = directionEl.value.trim();
    if ((!text && conceptImages.length === 0) || streaming) return;
    directionEl.value = "";
    if (text) addDirectionMessage("user", text);
    var selectedProducts = state.products.filter(function (p) { return p; });
    var prompt = "The user is setting up a content generation run with these settings:\n";
    prompt += "- Mode: " + state.mode.toUpperCase() + "\n";
    prompt += "- Type: " + state.type + "\n";
    prompt += "- Count: " + state.count + "\n";
    prompt += "- Aspect ratio: " + state.ratio + "\n";
    prompt += "- Product(s): " + (selectedProducts.length ? selectedProducts.join(", ") : "random") + "\n";
    if (conceptImages.length > 0) {
      prompt += "\nThey attached " + conceptImages.length + " concept/reference image(s). Read these files:\n";
      for (var i = 0; i < conceptImages.length; i++) prompt += "- " + conceptImages[i].path + "\n";
    }
    if (text) prompt += "\nTheir direction: \"" + text + "\"\n";
    prompt += "\nAcknowledge the current settings, then state what you understand in 2-3 bullet points. Do NOT ask questions -- just confirm your interpretation and say \"Hit Generate when ready.\" Fill in any missing details with sensible defaults based on DuberyMNL brand. Do NOT run any tools yet.";
    lockForm(); directionStatus.textContent = "Thinking...";
    var asstEl = addDirectionMessage("assistant", ""); var got = "";
    try {
      var res = await fetch("/api/agent/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt: prompt }) });
      if (!res.ok) throw new Error("HTTP " + res.status);
      var reader = res.body.getReader(); var decoder = new TextDecoder(); var buffer = "";
      while (true) {
        var result = await reader.read(); if (result.done) break;
        buffer += decoder.decode(result.value, { stream: true });
        var parts = buffer.split("\n\n"); buffer = parts.pop() || "";
        for (var j = 0; j < parts.length; j++) {
          var lines = parts[j].split("\n"), line = null;
          for (var k = 0; k < lines.length; k++) { if (lines[k].startsWith("data:")) { line = lines[k]; break; } }
          if (!line) continue;
          try { var obj = JSON.parse(line.slice(5).trim()); if (obj.text) { got += obj.text; asstEl.textContent = got; directionMessages.scrollTop = directionMessages.scrollHeight; } } catch (e) {}
        }
      }
      if (!got) asstEl.textContent = "(no response)";
      directionStatus.textContent = "";
    } catch (e) { asstEl.textContent = "[error] " + e.message; directionStatus.textContent = ""; }
    finally { unlockForm(); }
  }

  // =========================================================
  // OUTPUT RENDERING
  // =========================================================

  // Parse validation blocks from agent output
  function parseValidation(text) {
    var checks = [];
    var vRegex = /V(\d+)\s+([^:]+):\s*(PASS|FAIL)(?:\s*\(([^)]*)\))?/g;
    var match;
    while ((match = vRegex.exec(text)) !== null) {
      checks.push({ id: "V" + match[1], name: match[2].trim(), result: match[3], note: match[4] || "" });
    }
    var verdictMatch = text.match(/Verdict:\s*(PASS|FAIL)/);
    var verdict = verdictMatch ? verdictMatch[1] : null;
    return { checks: checks, verdict: verdict };
  }

  // Parse generation result details
  function parseResult(text) {
    var product = (text.match(/Product:\s*(.+)/m) || [])[1] || "";
    var category = (text.match(/Category:\s*(\S+)/m) || [])[1] || "";
    var scene = (text.match(/Scene:\s*(.+)/m) || [])[1] || "";
    var size = (text.match(/(\d+(?:\.\d+)?)\s*(?:KB|MB)/m) || [])[0] || "";
    var fidelity = (text.match(/Fidelity[^:]*:\s*(.+)/m) || [])[1] || "";
    return { product: product, category: category, scene: scene, size: size, fidelity: fidelity };
  }

  // Build a styled validation card
  function buildValidationCard(validation) {
    if (validation.checks.length === 0) return null;
    var card = document.createElement("div");
    card.className = "cg-val-card";
    var header = '<div class="cg-val-header"><span class="cg-val-title">Validation</span><span class="cg-val-verdict cg-val-' + (validation.verdict || "PASS").toLowerCase() + '">' + (validation.verdict || "") + '</span></div>';
    var checks = '<div class="cg-val-checks">';
    for (var i = 0; i < validation.checks.length; i++) {
      var c = validation.checks[i];
      var icon = c.result === "PASS" ? "\u2713" : "\u2717";
      var cls = c.result === "PASS" ? "pass" : "fail";
      checks += '<div class="cg-val-check cg-val-' + cls + '"><span class="cg-val-icon">' + icon + '</span><span class="cg-val-name">' + c.name + '</span>' + (c.note ? '<span class="cg-val-note">' + c.note + '</span>' : '') + '</div>';
    }
    checks += '</div>';
    card.innerHTML = header + checks;
    return card;
  }

  // Build an image result card
  function buildImageResultCard(imgPath, text) {
    var card = document.createElement("div");
    card.className = "cg-result-card";

    var details = parseResult(text);
    var validation = parseValidation(text);

    // Image
    var imgWrap = document.createElement("div");
    imgWrap.className = "cg-result-img-wrap";
    var img = document.createElement("img");
    img.src = "/api/images/" + imgPath;
    img.className = "cg-result-img";
    img.alt = imgPath.split("/").pop();
    img.loading = "lazy";
    img.onerror = function () { this.style.display = "none"; };
    img.addEventListener("click", function () {
      var modal = document.createElement("div");
      modal.className = "cg-lightbox";
      modal.innerHTML = '<img src="' + this.src + '" class="cg-lightbox-img"><button class="cg-lightbox-close">\u00D7</button>';
      modal.addEventListener("click", function (ev) {
        if (ev.target === modal || ev.target.classList.contains("cg-lightbox-close")) modal.remove();
      });
      document.body.appendChild(modal);
    });
    imgWrap.appendChild(img);

    // Details
    var detailsEl = document.createElement("div");
    detailsEl.className = "cg-result-details";
    var detailsHTML = '<div class="cg-result-filename">' + imgPath.split("/").pop() + '</div>';
    if (details.product) detailsHTML += '<div class="cg-result-meta"><span class="cg-result-meta-label">Product</span> ' + details.product + '</div>';
    if (details.category) detailsHTML += '<div class="cg-result-meta"><span class="cg-result-meta-label">Category</span> ' + details.category + '</div>';
    if (details.scene) detailsHTML += '<div class="cg-result-meta"><span class="cg-result-meta-label">Scene</span> ' + details.scene + '</div>';
    if (details.size) detailsHTML += '<div class="cg-result-meta"><span class="cg-result-meta-label">Size</span> ' + details.size + '</div>';
    if (details.fidelity) detailsHTML += '<div class="cg-result-meta cg-result-fidelity">' + details.fidelity + '</div>';
    detailsEl.innerHTML = detailsHTML;

    // View prompt link -- derive prompt path from image (same stem + _prompt.json)
    var promptPath = imgPath.replace(/\.(png|jpe?g|webp|gif)$/i, "_prompt.json");
    var viewPrompt = document.createElement("button");
    viewPrompt.className = "btn cg-view-prompt";
    viewPrompt.textContent = "View prompt";
    viewPrompt.style.cssText = "margin-top:6px;font-size:11px;padding:4px 8px;";
    viewPrompt.addEventListener("click", function () { showPromptModal(promptPath); });
    detailsEl.appendChild(viewPrompt);

    card.appendChild(imgWrap);
    card.appendChild(detailsEl);

    // Validation
    var valCard = buildValidationCard(validation);
    if (valCard) card.appendChild(valCard);

    return card;
  }

  // Append a Save button after a successful generation. Clicking archives
  // images + prompt JSONs + concepts into contents/runs/<ts>_<mode>/.
  function addSaveRunButton(images, promptPaths, conceptPaths, directionText) {
    if (!images || images.length === 0) return;
    var existing = document.getElementById("cg-save-row");
    if (existing) existing.remove();
    var row = document.createElement("div");
    row.className = "cg-save-row";
    row.id = "cg-save-row";
    var btn = document.createElement("button");
    btn.className = "cg-save-btn";
    btn.textContent = "Save run";
    btn.addEventListener("click", async function () {
      btn.disabled = true;
      btn.textContent = "Saving...";
      try {
        var res = await fetch("/api/save-run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            images: images,
            prompt_paths: promptPaths,
            concept_paths: conceptPaths,
            aspect_ratio: state.ratio,
            mode: state.mode,
            type: state.type,
            count: images.length,
            products: state.products.filter(function (p) { return p; }),
            direction: directionText || "",
          }),
        });
        var data = await res.json();
        if (data.ok) {
          btn.classList.add("saved");
          btn.textContent = "Saved \u2713  " + (data.run_dir || "");
          if (window.showToast) window.showToast("Saved to " + data.run_dir, "ok");
        } else {
          btn.disabled = false;
          btn.textContent = "Save run";
          if (window.showToast) window.showToast(data.error || "Save failed", "bad");
        }
      } catch (e) {
        btn.disabled = false;
        btn.textContent = "Save run";
        if (window.showToast) window.showToast("Save failed: " + e.message, "bad");
      }
    });
    row.appendChild(btn);
    outputBody.appendChild(row);
  }

  // Fetch a text file from the server and show it in a modal.
  function showPromptModal(relPath) {
    var modal = document.createElement("div");
    modal.className = "cg-lightbox";
    var box = document.createElement("div");
    box.className = "cg-prompt-modal-content";
    box.innerHTML = '<pre>Loading ' + relPath + '...</pre>';
    modal.appendChild(box);
    modal.addEventListener("click", function (ev) { if (ev.target === modal) modal.remove(); });
    var closeBtn = document.createElement("button");
    closeBtn.className = "cg-lightbox-close";
    closeBtn.textContent = "\u00D7";
    closeBtn.addEventListener("click", function () { modal.remove(); });
    modal.appendChild(closeBtn);
    document.body.appendChild(modal);

    fetch("/api/file-content/" + relPath)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.text();
      })
      .then(function (text) {
        try { text = JSON.stringify(JSON.parse(text), null, 2); } catch (e) {}
        var pre = box.querySelector("pre");
        pre.textContent = text;
      })
      .catch(function (e) {
        var pre = box.querySelector("pre");
        pre.textContent = "[error loading " + relPath + "]\n" + e.message;
      });
  }

  // --- detect GENERATED image paths only (contents/new/ or contents/runs/) ---
  var seenImages = new Set();
  var generatedPaths = []; // track generated image paths for history

  function extractImages(text) {
    // Match contents/new/ and contents/runs/ -- not assets/prodrefs
    var imgRegex = /(?:[A-Za-z]:[\\\/](?:[^\s"'`,)]+[\\\/])?)?contents[\\\/](?:new|runs)[\\\/][^\s"'`,)]+\.(?:png|jpg|jpeg|webp)/gi;
    var rawMatches = text.match(imgRegex);
    if (!rawMatches) return;
    var matches = rawMatches.map(function (m) {
      var idx = m.search(/contents[\\\/]/i);
      if (idx > 0) m = m.substring(idx);
      return m.replace(/\\/g, "/");
    });

    var resultsArea = document.getElementById("cg-results-area");
    if (!resultsArea) {
      resultsArea = document.createElement("div");
      resultsArea.id = "cg-results-area";
      resultsArea.className = "cg-results-area";
      outputBody.appendChild(resultsArea);
    }

    for (var i = 0; i < matches.length; i++) {
      var m = matches[i];
      if (seenImages.has(m)) continue;
      seenImages.add(m);
      generatedPaths.push(m);
      var card = buildImageResultCard(m, text);
      resultsArea.appendChild(card);
      appendPromptRefCard(m);
    }
    updateImageCount();
  }

  // Append a "Prompt" card to the top ref-images row for each generated image.
  function appendPromptRefCard(imgPath) {
    var refImages = document.querySelector(".cg-ref-section .cg-ref-images");
    if (!refImages) {
      // No ref section yet (no concept/prodref used) -- create a minimal one.
      var outEl = document.getElementById("cg-output-body");
      var section = document.createElement("div");
      section.className = "cg-ref-section";
      section.innerHTML = '<div class="cg-ref-label">Reference used</div><div class="cg-ref-images"></div>';
      if (outEl.firstChild) outEl.insertBefore(section, outEl.firstChild);
      else outEl.appendChild(section);
      refImages = section.querySelector(".cg-ref-images");
    }
    var promptPath = imgPath.replace(/\.(png|jpe?g|webp|gif)$/i, "_prompt.json");
    var wrap = document.createElement("div");
    wrap.className = "cg-ref-item";
    wrap.innerHTML = '<div class="cg-ref-prompt" title="' + promptPath + '">{ } Prompt</div><div class="cg-ref-tag">Prompt</div>';
    wrap.querySelector(".cg-ref-prompt").addEventListener("click", function () { showPromptModal(promptPath); });
    refImages.appendChild(wrap);
  }

  function updateImageCount() {
    var imgs = outputBody.querySelectorAll(".cg-result-img");
    imageCount.textContent = imgs.length ? imgs.length + " image" + (imgs.length > 1 ? "s" : "") : "";
  }

  // =========================================================
  // HISTORY
  // =========================================================
  function addHistoryBatch(paths) {
    if (!paths || !paths.length) return;
    historyArea.classList.remove("hidden");
    var batch = document.createElement("div"); batch.className = "cg-history-batch";
    var ts = document.createElement("div"); ts.className = "cg-history-ts"; ts.textContent = new Date().toLocaleTimeString();
    batch.appendChild(ts);
    var row = document.createElement("div"); row.className = "cg-history-row";
    for (var i = 0; i < paths.length; i++) {
      var thumb = document.createElement("img");
      thumb.src = "/api/images/" + paths[i];
      thumb.className = "cg-history-img";
      thumb.alt = paths[i].split("/").pop();
      thumb.addEventListener("click", function () {
        var modal = document.createElement("div");
        modal.className = "cg-lightbox";
        modal.innerHTML = '<img src="' + this.src + '" class="cg-lightbox-img"><button class="cg-lightbox-close">\u00D7</button>';
        modal.addEventListener("click", function (ev) {
          if (ev.target === modal || ev.target.classList.contains("cg-lightbox-close")) modal.remove();
        });
        document.body.appendChild(modal);
      });
      row.appendChild(thumb);
    }
    batch.appendChild(row);
    if (historyArea.firstChild) historyArea.insertBefore(batch, historyArea.firstChild);
    else historyArea.appendChild(batch);
    var batches = historyArea.querySelectorAll(".cg-history-batch");
    if (historyCount) historyCount.textContent = batches.length + " run" + (batches.length > 1 ? "s" : "");
  }

  function archiveCurrentToHistory() {
    addHistoryBatch(generatedPaths);
  }

  // =========================================================
  // CLEAR
  // =========================================================
  resetAgentBtn.addEventListener("click", async function () {
    if (streaming) return;
    resetAgentBtn.textContent = "Resetting...";
    resetAgentBtn.disabled = true;
    try {
      await fetch("/api/agent/reset", { method: "POST" });
      if (window.showToast) window.showToast("Agent session reset", "ok");
    } catch (e) {
      if (window.showToast) window.showToast("Reset failed", "bad");
    } finally {
      resetAgentBtn.textContent = "Reset agent";
      resetAgentBtn.disabled = false;
    }
  });

  clearBtn.addEventListener("click", function () {
    if (streaming) return;
    thinkingStatus.textContent = "";
    outputBody.innerHTML = '<div class="cg-ready-hint" id="cg-ready-hint">Ready: <span id="cg-ready-summary"></span></div>';
    readySummary = document.getElementById("cg-ready-summary");
    updateReadyHint();
    imageCount.textContent = "";
    seenImages.clear();
    directionMessages.innerHTML = "";
    conceptImages = [];
    renderAttachments();
    directionStatus.textContent = "";
  });

  // =========================================================
  // LOCK / UNLOCK
  // =========================================================
  function lockForm() {
    streaming = true;
    genBtn.textContent = "Stop";
    genBtn.classList.add("cg-stop-mode");
    genBtn.disabled = false;
    sendBtn.disabled = true; clearBtn.disabled = true; directionSendBtn.disabled = true;
    addProductBtn.classList.add("disabled");
    document.querySelectorAll(".cg-pill, .cg-step-btn, .cg-product-select, .cg-product-remove").forEach(function (el) {
      el.classList.add("disabled"); if (el.tagName === "SELECT") el.disabled = true;
    });
  }
  function unlockForm() {
    streaming = false;
    currentController = null;
    genBtn.textContent = "Generate";
    genBtn.classList.remove("cg-stop-mode");
    genBtn.disabled = false; sendBtn.disabled = false; clearBtn.disabled = false; directionSendBtn.disabled = false;
    addProductBtn.classList.remove("disabled");
    document.querySelectorAll(".cg-pill, .cg-step-btn, .cg-product-select, .cg-product-remove").forEach(function (el) {
      el.classList.remove("disabled"); if (el.tagName === "SELECT") el.disabled = false;
    });
  }

  // =========================================================
  // SSE STREAM
  // =========================================================
  async function streamPrompt(prompt) {
    if (streaming) return;
    lockForm();

    // Show concept + prodref references at top of output
    var refHTML = "";
    var selectedProducts = state.products.filter(function (p) { return p; });
    var hasRefs = pendingConcepts.length > 0 || selectedProducts.length > 0;
    if (hasRefs) {
      refHTML = '<div class="cg-ref-section"><div class="cg-ref-label">Reference used</div><div class="cg-ref-images">';
      for (var r = 0; r < pendingConcepts.length; r++) {
        refHTML += '<div class="cg-ref-item"><img src="' + pendingConcepts[r].dataUrl + '" class="cg-ref-img" alt="concept" onclick="(function(s){var m=document.createElement(\'div\');m.className=\'cg-lightbox\';m.innerHTML=\'<img src=\\\'\'+s+\'\\\' class=cg-lightbox-img><button class=cg-lightbox-close>\u00D7</button>\';m.onclick=function(e){if(e.target===m||e.target.classList.contains(\'cg-lightbox-close\'))m.remove()};document.body.appendChild(m)})(this.src)"><div class="cg-ref-tag">Concept</div></div>';
      }
      for (var p = 0; p < selectedProducts.length; p++) {
        var prodrefUrl = "/api/images/contents/assets/prodref-kraft/" + selectedProducts[p] + "/01-hero.png";
        refHTML += '<div class="cg-ref-item"><img src="' + prodrefUrl + '" class="cg-ref-img" alt="prodref" onclick="(function(s){var m=document.createElement(\'div\');m.className=\'cg-lightbox\';m.innerHTML=\'<img src=\\\'\'+s+\'\\\' class=cg-lightbox-img><button class=cg-lightbox-close>\u00D7</button>\';m.onclick=function(e){if(e.target===m||e.target.classList.contains(\'cg-lightbox-close\'))m.remove()};document.body.appendChild(m)})(this.src)"><div class="cg-ref-tag">Prodref</div></div>';
      }
      refHTML += '</div></div>';
      pendingConcepts = [];
    }
    outputBody.innerHTML = refHTML +
      '<div class="cg-progress-wrap expanded" id="cg-progress-wrap">' +
        '<div class="cg-progress-toggle" id="cg-progress-toggle">' +
          '<span class="cg-progress-arrow">&#9654;</span>' +
          '<span class="cg-progress-summary" id="cg-progress-summary">Running pipeline...</span>' +
        '</div>' +
        '<div class="cg-output-log" id="cg-output-log"></div>' +
      '</div>';
    document.getElementById("cg-progress-toggle").addEventListener("click", function () {
      document.getElementById("cg-progress-wrap").classList.toggle("expanded");
    });
    // Add typing dots below progress
    var dotsEl = document.createElement("div");
    dotsEl.id = "cg-typing-dots";
    dotsEl.className = "cg-typing-dots";
    dotsEl.innerHTML = "<span></span><span></span><span></span>";
    outputBody.appendChild(dotsEl);
    thinkingStatus.textContent = "Running...";
    imageCount.textContent = "";
    seenImages.clear();
    generatedPaths = [];

    var got = "";
    currentController = new AbortController();

    try {
      var res = await fetch("/api/agent/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt: prompt }), signal: currentController.signal });
      if (!res.ok) throw new Error("HTTP " + res.status);
      if (!res.body) throw new Error("no stream body");
      var reader = res.body.getReader(); var decoder = new TextDecoder(); var buffer = "";

      while (true) {
        var result = await reader.read(); if (result.done) break;
        buffer += decoder.decode(result.value, { stream: true });
        var parts = buffer.split("\n\n"); buffer = parts.pop() || "";
        for (var i = 0; i < parts.length; i++) {
          var lines = parts[i].split("\n"), line = null;
          for (var j = 0; j < lines.length; j++) { if (lines[j].startsWith("data:")) { line = lines[j]; break; } }
          if (!line) continue;
          try {
            var obj = JSON.parse(line.slice(5).trim());
            if (obj.text) {
              got += obj.text;
              var logEl = document.getElementById("cg-output-log");
              if (logEl) { logEl.innerHTML = renderMarkdown(got); logEl.scrollTop = logEl.scrollHeight; }
              extractImages(got);
            } else if (obj.error) {
              var logEl2 = document.getElementById("cg-output-log");
              if (logEl2) logEl2.innerHTML += '<div class="cg-error">[error] ' + obj.error + "</div>";
              thinkingStatus.textContent = "Error";
            }
          } catch (e) {}
        }
      }
      if (!got) { var logEl3 = document.getElementById("cg-output-log"); if (logEl3) logEl3.innerHTML = '<div class="cg-error">(no response)</div>'; }
      thinkingStatus.textContent = "Done";
      // Remove typing dots
      var dots = document.getElementById("cg-typing-dots");
      if (dots) dots.remove();
      // Collapse progress and show summary
      var wrap = document.getElementById("cg-progress-wrap");
      var summary = document.getElementById("cg-progress-summary");
      if (wrap) wrap.classList.remove("expanded");
      if (summary) {
        var imgCount = generatedPaths.length;
        summary.textContent = imgCount > 0
          ? "Pipeline complete -- " + imgCount + " image" + (imgCount > 1 ? "s" : "") + " generated"
          : "Pipeline complete -- click to view details";
      }
      archiveCurrentToHistory();
      // Log generation event with full details
      if (generatedPaths.length > 0) {
        var dirMsgsLog = directionMessages.querySelectorAll(".cg-dir-msg");
        var dirText = "";
        for (var d = 0; d < dirMsgsLog.length; d++) dirText += dirMsgsLog[d].textContent + "\n";
        var promptPaths = generatedPaths.map(function (p) {
          return p.replace(/\.(png|jpe?g|webp|gif)$/i, "_prompt.json");
        });
        var lastConcepts = (pendingConcepts || []).map(function (c) { return c.path; });
        fetch("/api/log-generation", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            images: generatedPaths,
            prompt_paths: promptPaths,
            aspect_ratio: state.ratio,
            mode: state.mode,
            type: state.type,
            count: generatedPaths.length,
            products: state.products.filter(function (p) { return p; }),
            direction: dirText.trim(),
            concept_paths: lastConcepts,
          }),
        }).catch(function () {});
        if (window.showToast) window.showToast("Generated " + generatedPaths.length + " image" + (generatedPaths.length > 1 ? "s" : ""), "ok");
        addSaveRunButton(generatedPaths.slice(), promptPaths, lastConcepts, dirText.trim());
      }
    } catch (e) {
      var dots2 = document.getElementById("cg-typing-dots");
      if (dots2) dots2.remove();
      if (e.name === "AbortError") {
        thinkingStatus.textContent = "Stopped";
        var logElStop = document.getElementById("cg-output-log");
        if (logElStop) logElStop.innerHTML += '<div class="cg-error">[stopped by user]</div>';
        if (generatedPaths.length > 0) archiveCurrentToHistory();
      } else {
        var logEl4 = document.getElementById("cg-output-log");
        if (logEl4) logEl4.innerHTML += '<div class="cg-error">[fetch error] ' + e.message + "</div>";
        thinkingStatus.textContent = "Error";
      }
    } finally { unlockForm(); }
  }

  // =========================================================
  // MARKDOWN
  // =========================================================
  function renderMarkdown(text) {
    var html = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, function (_, l, c) { return '<pre class="cg-code"><code>' + c.trim() + "</code></pre>"; });
    html = html.replace(/`([^`]+)`/g, '<code class="cg-inline-code">$1</code>');
    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/^### (.+)$/gm, '<div class="cg-h3">$1</div>');
    html = html.replace(/^## (.+)$/gm, '<div class="cg-h2">$1</div>');
    html = html.replace(/^# (.+)$/gm, '<div class="cg-h1">$1</div>');
    html = html.replace(/^[-*] (.+)$/gm, '<div class="cg-li">$1</div>');
    html = html.replace(/^\d+\. (.+)$/gm, '<div class="cg-li cg-li-num">$1</div>');
    html = html.replace(/\n\n/g, '<div class="cg-gap"></div>');
    html = html.replace(/\n/g, "<br>");
    return html;
  }

  // =========================================================
  // GENERATE
  // =========================================================
  genBtn.addEventListener("click", function () {
    if (streaming && currentController) {
      currentController.abort();
      return;
    }
    var selectedProducts = state.products.filter(function (p) { return p; });
    var dirMsgs = directionMessages.querySelectorAll(".cg-dir-msg");
    var dirContext = "";
    for (var i = 0; i < dirMsgs.length; i++) {
      dirContext += (dirMsgs[i].classList.contains("cg-dir-user") ? "User" : "Assistant") + ": " + dirMsgs[i].textContent + "\n";
    }
    var prompt = "Generate " + state.count + " DuberyMNL " + state.mode.toUpperCase() + " content (" + state.type + "-focused).";
    prompt += "\nAspect ratio: " + state.ratio + " (set \"aspect_ratio\": \"" + state.ratio + "\" on every prompt JSON before calling generate_vertex.py).";
    if (selectedProducts.length > 0) prompt += "\nProducts: " + selectedProducts.join(", ");
    if (conceptImages.length > 0) {
      prompt += "\nConcept/reference images to read:";
      for (var j = 0; j < conceptImages.length; j++) prompt += "\n- " + conceptImages[j].path;
    }
    if (dirContext) prompt += "\n\nDirection conversation:\n" + dirContext;
    var extraDir = directionEl.value.trim();
    if (extraDir) { prompt += "\nAdditional direction: " + extraDir; directionEl.value = ""; }
    if (state.mode === "bespoke") {
      prompt += "\n\nThis is a BESPOKE concept recreation. Instructions:";
      prompt += "\n1. Read the concept/reference image to understand the visual direction.";
      prompt += "\n2. Use the selected product's kraft prodref from contents/assets/prodref-kraft/ as the locked product asset.";
      prompt += "\n3. Build a v3 JSON prompt (product-as-locked-asset schema) that recreates the concept with DuberyMNL branding -- match the concept's composition, mood, and color palette while adapting accents to the product's actual colors.";
      prompt += "\n4. Skip the randomizer entirely -- scene variables come from the concept image, not from banks.";
      prompt += "\n5. Read .claude/skills/dubery-fidelity-prompt/SKILL.md for the exact JSON schema to follow.";
      prompt += "\n6. Set \"aspect_ratio\": \"" + state.ratio + "\" in the prompt JSON before generating.";
      prompt += "\n7. Call: python tools/image_gen/generate_vertex.py <prompt_json_file>";
      prompt += "\n8. Report the output file path.";
      if (!conceptImages.length && !pendingConcepts.length && !dirContext) {
        prompt += "\n\nNOTE: No concept image was attached. Ask the user to paste a reference image in the Direction chat first.";
      }
    } else if (state.mode === "ugc") {
      var prodFlag = selectedProducts.length === 1 ? " --product " + selectedProducts[0] : "";
      prompt += "\n\n=== MANDATORY PIPELINE -- follow every step exactly. Do NOT write your own prompts. Do NOT call generate_vertex.py without a saved prompt JSON file. ===";
      prompt += "\n\nUGC PIPELINE:";
      prompt += "\nStep 1 — Run the randomizer (it outputs a JSON array of scene assignments to stdout):";
      prompt += "\n  python tools/image_gen/v3_randomizer.py --type " + state.type + " --count " + state.count + prodFlag + " > .tmp/ugc_batch.json";
      prompt += "\n\nStep 2 — Read .tmp/ugc_batch.json. It is a JSON array. Process each item one at a time:";
      prompt += "\n  a. Load product spec: read contents/assets/product-specs.json, get the entry for assignment.product_key";
      prompt += "\n  b. Filter required_details by assignment.visible_details (keep only indexed entries)";
      prompt += "\n  c. Load the prodref sidecar JSON at assignment.prodref_sidecar (frame_direction, visible_details)";
      prompt += "\n  d. Read .claude/skills/dubery-fidelity-prompt/SKILL.md for the exact JSON schema";
      prompt += "\n  e. Build the v3 prompt JSON using the scene in assignment.scene + filtered required_details + frame_direction";
      prompt += "\n  f. Set top-level \"aspect_ratio\": \"" + state.ratio + "\" in the JSON";
      prompt += "\n  g. Set \"image_input\": [assignment.prodref] in the JSON";
      prompt += "\n  h. Write to .tmp/ugc_{batch_index}_prompt.json (use assignment.batch_index for the filename)";
      prompt += "\n\nStep 3 — Generate each image in sequence (one at a time, wait for each to finish):";
      prompt += "\n  python tools/image_gen/generate_vertex.py .tmp/ugc_{batch_index}_prompt.json";
      prompt += "\n\nStep 4 — After all images are done, print the full output path of each generated image file.";
    } else {
      // brand
      prompt += "\n\n=== MANDATORY PIPELINE -- follow every step exactly. Do NOT write your own prompts. Do NOT call generate_vertex.py without a saved prompt JSON file. ===";
      prompt += "\n\nBRAND PIPELINE:";
      prompt += "\nStep 1 — Run the batch randomizer (outputs a JSON array of skill assignments to stdout):";
      prompt += "\n  python tools/image_gen/batch_randomizer.py --type mix --count " + state.count + " > .tmp/brand_batch.json";
      prompt += "\n\nStep 2 — Read .tmp/brand_batch.json. It is a JSON array. Process each item one at a time:";
      prompt += "\n  a. Note the skill field (brand-bold, brand-callout, or brand-collection)";
      prompt += "\n  b. Read .claude/skills/dubery-brand-{skill}/SKILL.md for the prompt-building rules and JSON schema";
      prompt += "\n  c. Build the v3 prompt JSON following that skill's schema for the given product + layout";
      prompt += "\n  d. Set top-level \"aspect_ratio\": \"" + state.ratio + "\" in the JSON";
      prompt += "\n  e. Write to .tmp/brand_{i}_prompt.json (use array index i for the filename)";
      prompt += "\n\nStep 3 — Generate each image in sequence (one at a time, wait for each to finish):";
      prompt += "\n  python tools/image_gen/generate_vertex.py .tmp/brand_{i}_prompt.json";
      prompt += "\n\nStep 4 — After all images are done, print the full output path of each generated image file.";
    }

    // Move concept images to output as "Reference used", then clear from direction
    if (conceptImages.length > 0) {
      pendingConcepts = conceptImages.slice();
      conceptImages = [];
      renderAttachments();
    }

    streamPrompt(prompt);
  });

  // =========================================================
  // FEEDBACK
  // =========================================================
  function sendFollowUp() {
    var text = inputEl.value.trim(); if (!text || streaming) return;
    inputEl.value = ""; inputEl.style.height = "auto";
    streamFeedback(text);
  }

  async function streamFeedback(prompt) {
    if (streaming) return;
    lockForm();
    thinkingStatus.textContent = "Running...";

    // Append a feedback log section without clearing existing output
    var feedbackLog = document.createElement("div");
    feedbackLog.className = "cg-feedback-log";
    feedbackLog.innerHTML = '<div class="cg-feedback-prompt">' + prompt.replace(/&/g,"&amp;").replace(/</g,"&lt;") + '</div>';
    outputBody.appendChild(feedbackLog);

    var responseEl = document.createElement("div");
    responseEl.className = "cg-feedback-response";
    feedbackLog.appendChild(responseEl);

    var fdots = document.createElement("div");
    fdots.id = "cg-typing-dots";
    fdots.className = "cg-typing-dots";
    fdots.innerHTML = "<span></span><span></span><span></span>";
    feedbackLog.appendChild(fdots);

    var got = "";
    currentController = new AbortController();
    try {
      var res = await fetch("/api/agent/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt: prompt }), signal: currentController.signal });
      if (!res.ok) throw new Error("HTTP " + res.status);
      var reader = res.body.getReader(); var decoder = new TextDecoder(); var buffer = "";
      while (true) {
        var result = await reader.read(); if (result.done) break;
        buffer += decoder.decode(result.value, { stream: true });
        var parts = buffer.split("\n\n"); buffer = parts.pop() || "";
        for (var i = 0; i < parts.length; i++) {
          var lines = parts[i].split("\n"), line = null;
          for (var j = 0; j < lines.length; j++) { if (lines[j].startsWith("data:")) { line = lines[j]; break; } }
          if (!line) continue;
          try {
            var obj = JSON.parse(line.slice(5).trim());
            if (obj.text) { got += obj.text; responseEl.innerHTML = renderMarkdown(got); outputBody.scrollTop = outputBody.scrollHeight; }
          } catch (e) {}
        }
      }
      if (!got) responseEl.innerHTML = "(no response)";
      thinkingStatus.textContent = "Done";
      var fd = document.getElementById("cg-typing-dots"); if (fd) fd.remove();
      var prevLen = generatedPaths.length;
      extractImages(got);
      // Log any newly discovered images from this regen to history
      var newPaths = generatedPaths.slice(prevLen);
      if (newPaths.length) {
        var newPromptPaths = newPaths.map(function (p) { return p.replace(/\.(png|jpe?g|webp|gif)$/i, "_prompt.json"); });
        fetch("/api/log-generation", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            images: newPaths,
            prompt_paths: newPromptPaths,
            aspect_ratio: state.ratio,
            mode: state.mode,
            type: state.type,
            count: newPaths.length,
            products: state.products.filter(function (p) { return p; }),
            direction: "[regen] " + prompt,
            concept_paths: [],
          }),
        }).catch(function () {});
        addHistoryBatch(newPaths);
        if (window.showToast) window.showToast("Regenerated " + newPaths.length + " image" + (newPaths.length > 1 ? "s" : ""), "ok");
      }
    } catch (e) {
      var fdErr = document.getElementById("cg-typing-dots"); if (fdErr) fdErr.remove();
      if (e.name === "AbortError") {
        responseEl.innerHTML += '<span class="cg-error">[stopped]</span>';
        thinkingStatus.textContent = "Stopped";
      } else {
        responseEl.innerHTML = '<span class="cg-error">[error] ' + e.message + '</span>';
        thinkingStatus.textContent = "Error";
      }
    } finally { unlockForm(); }
  }
  sendBtn.addEventListener("click", sendFollowUp);
  inputEl.addEventListener("keydown", function (ev) { if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); sendFollowUp(); } });
  inputEl.addEventListener("input", function () { inputEl.style.height = "auto"; inputEl.style.height = Math.min(inputEl.scrollHeight, 80) + "px"; });

  // =========================================================
  // LOAD HISTORY FROM SERVER
  // =========================================================
  async function loadHistory() {
    try {
      var res = await fetch("/api/generation-history");
      var history = await res.json();
      if (!history.length) return;

      historyArea.innerHTML = "";
      historyArea.classList.remove("hidden");

      for (var i = history.length - 1; i >= 0; i--) {
        var entry = history[i];
        if (!entry.images || !entry.images.length) continue;

        var batch = document.createElement("div"); batch.className = "cg-history-batch";

        var ts = document.createElement("div"); ts.className = "cg-history-ts";
        var d = new Date(entry.ts);
        ts.textContent = d.toLocaleDateString() + " " + d.toLocaleTimeString();
        batch.appendChild(ts);

        var row = document.createElement("div"); row.className = "cg-history-row";
        for (var j = 0; j < entry.images.length; j++) {
          var thumb = document.createElement("img");
          thumb.src = "/api/images/" + entry.images[j];
          thumb.className = "cg-history-img";
          thumb.alt = entry.images[j].split("/").pop();
          thumb.title = (entry.mode || "").toUpperCase() + " " + (entry.type || "") + (entry.products && entry.products.length ? " | " + entry.products.join(", ") : "");
          thumb.addEventListener("click", function () {
            var modal = document.createElement("div"); modal.className = "cg-lightbox";
            modal.innerHTML = '<img src="' + this.src + '" class="cg-lightbox-img"><button class="cg-lightbox-close">\u00D7</button>';
            modal.addEventListener("click", function (ev) { if (ev.target === modal || ev.target.classList.contains("cg-lightbox-close")) modal.remove(); });
            document.body.appendChild(modal);
          });
          row.appendChild(thumb);
        }
        batch.appendChild(row);
        historyArea.appendChild(batch);
      }

      var batches = historyArea.querySelectorAll(".cg-history-batch");
      if (historyCount) historyCount.textContent = batches.length + " run" + (batches.length > 1 ? "s" : "");
    } catch (e) { /* silent */ }
  }

  // =========================================================
  // TAB LIFECYCLE
  // =========================================================
  document.addEventListener("tab:activated", function (ev) {
    if (ev.detail && ev.detail.tab === "content-gen") { if (allProducts.length === 0) loadProducts(); loadHistory(); directionEl.focus(); }
  });
  loadProducts();
  loadHistory();
})();
