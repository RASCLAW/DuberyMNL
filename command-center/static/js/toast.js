// Toast notification system. Global: window.showToast(message, type)
// type: "ok" | "warn" | "bad" | "info" (default: "info")
(function () {
  "use strict";

  var container = document.getElementById("toast-container");
  if (!container) return;

  var DURATION = 4000;
  var FADE_MS = 300;

  window.showToast = function (message, type) {
    type = type || "info";
    var el = document.createElement("div");
    el.className = "toast toast-" + type;
    el.textContent = message;

    container.appendChild(el);

    // Trigger entrance animation
    requestAnimationFrame(function () {
      el.classList.add("toast-visible");
    });

    // Auto-dismiss
    setTimeout(function () {
      el.classList.remove("toast-visible");
      setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, FADE_MS);
    }, DURATION);

    // Click to dismiss
    el.addEventListener("click", function () {
      el.classList.remove("toast-visible");
      setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, FADE_MS);
    });
  };
})();
