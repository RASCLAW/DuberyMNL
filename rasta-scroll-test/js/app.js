/* ============================================
   DUBERY Rasta Red - Scroll-Driven Experience
   ============================================ */

const FRAME_COUNT = 144;
const FRAME_SPEED = 2.0;
const IMAGE_SCALE = 0.88;

// DOM refs
const loader = document.getElementById("loader");
const loaderBar = document.getElementById("loader-bar");
const loaderPercent = document.getElementById("loader-percent");
const heroSection = document.getElementById("hero");
const canvasWrap = document.getElementById("canvas-wrap");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const scrollContainer = document.getElementById("scroll-container");
const darkOverlay = document.getElementById("dark-overlay");

// State
const frames = [];
let currentFrame = -1;
let bgColor = "#0a0a0a";

// ===========================
// 1. LENIS SMOOTH SCROLL
// ===========================
const lenis = new Lenis({
  duration: 1.2,
  easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  smoothWheel: true,
});
lenis.on("scroll", ScrollTrigger.update);
gsap.ticker.add((time) => lenis.raf(time * 1000));
gsap.ticker.lagSmoothing(0);

// ===========================
// 2. FRAME PRELOADER
// ===========================
function preloadFrames() {
  let loaded = 0;
  const firstBatch = 10;

  return new Promise((resolve) => {
    for (let i = 1; i <= FRAME_COUNT; i++) {
      const img = new Image();
      img.src = `frames/frame_${String(i).padStart(4, "0")}.webp`;
      img.onload = () => {
        loaded++;
        const pct = Math.round((loaded / FRAME_COUNT) * 100);
        loaderBar.style.width = pct + "%";
        loaderPercent.textContent = pct + "%";

        if (loaded === firstBatch) {
          // Show first frame immediately
          sampleBgColor(frames[0]);
          resizeCanvas();
          drawFrame(0);
        }
        if (loaded === FRAME_COUNT) resolve();
      };
      img.onerror = () => {
        loaded++;
        if (loaded === FRAME_COUNT) resolve();
      };
      frames[i - 1] = img;
    }
  });
}

// ===========================
// 3. CANVAS RENDERER
// ===========================
function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  canvas.width = window.innerWidth * dpr;
  canvas.height = window.innerHeight * dpr;
  canvas.style.width = window.innerWidth + "px";
  canvas.style.height = window.innerHeight + "px";
  ctx.scale(dpr, dpr);
  if (currentFrame >= 0) drawFrame(currentFrame);
}

function sampleBgColor(img) {
  if (!img || !img.naturalWidth) return;
  const tmp = document.createElement("canvas");
  tmp.width = img.naturalWidth;
  tmp.height = img.naturalHeight;
  const tctx = tmp.getContext("2d");
  tctx.drawImage(img, 0, 0);
  const d = tctx.getImageData(2, 2, 1, 1).data;
  bgColor = `rgb(${d[0]},${d[1]},${d[2]})`;
}

function drawFrame(index) {
  const img = frames[index];
  if (!img || !img.naturalWidth) return;
  const cw = window.innerWidth;
  const ch = window.innerHeight;
  const iw = img.naturalWidth;
  const ih = img.naturalHeight;
  const scale = Math.max(cw / iw, ch / ih) * IMAGE_SCALE;
  const dw = iw * scale;
  const dh = ih * scale;
  const dx = (cw - dw) / 2;
  const dy = (ch - dh) / 2;

  ctx.fillStyle = bgColor;
  ctx.fillRect(0, 0, cw, ch);
  ctx.drawImage(img, dx, dy, dw, dh);
}

window.addEventListener("resize", resizeCanvas);

// ===========================
// 4. FRAME-TO-SCROLL BINDING
// ===========================
function initFrameScroll() {
  ScrollTrigger.create({
    trigger: scrollContainer,
    start: "top top",
    end: "bottom bottom",
    scrub: true,
    onUpdate: (self) => {
      const accelerated = Math.min(self.progress * FRAME_SPEED, 1);
      const index = Math.min(
        Math.floor(accelerated * FRAME_COUNT),
        FRAME_COUNT - 1
      );
      if (index !== currentFrame) {
        currentFrame = index;
        // Sample bg color every ~20 frames
        if (index % 20 === 0) sampleBgColor(frames[index]);
        requestAnimationFrame(() => drawFrame(currentFrame));
      }
    },
  });
}

// ===========================
// 5. HERO CIRCLE-WIPE REVEAL
// ===========================
function initHeroTransition() {
  ScrollTrigger.create({
    trigger: scrollContainer,
    start: "top top",
    end: "bottom bottom",
    scrub: true,
    onUpdate: (self) => {
      const p = self.progress;
      // Hero fades out, canvas is always visible behind it
      heroSection.style.opacity = Math.max(0, 1 - p * 15);
    },
  });
}

// ===========================
// 6. SECTION ANIMATION SYSTEM
// ===========================
function setupSections() {
  const sections = document.querySelectorAll(".scroll-section");
  const containerHeight = scrollContainer.offsetHeight;

  sections.forEach((section) => {
    const type = section.dataset.animation;
    const persist = section.dataset.persist === "true";
    const enter = parseFloat(section.dataset.enter) / 100;
    const leave = parseFloat(section.dataset.leave) / 100;
    const mid = (enter + leave) / 2;

    // Position section at midpoint
    if (type !== "horizontal-scroll") {
      section.style.top = mid * containerHeight + "px";
      section.style.transform = "translateY(-50%)";
      section.style.height = "auto";
    } else {
      section.style.top = mid * containerHeight - window.innerHeight / 2 + "px";
    }

    const children = section.querySelectorAll(
      ".section-label, .section-heading, .section-body, .section-note, .cta-button, .stat, .panel-content"
    );

    const tl = gsap.timeline({ paused: true });

    switch (type) {
      case "fade-up":
        tl.from(children, { y: 50, opacity: 0, stagger: 0.12, duration: 0.9, ease: "power3.out" });
        break;
      case "slide-left":
        tl.from(children, { x: -80, opacity: 0, stagger: 0.14, duration: 0.9, ease: "power3.out" });
        break;
      case "slide-right":
        tl.from(children, { x: 80, opacity: 0, stagger: 0.14, duration: 0.9, ease: "power3.out" });
        break;
      case "scale-up":
        tl.from(children, { scale: 0.85, opacity: 0, stagger: 0.12, duration: 1.0, ease: "power2.out" });
        break;
      case "stagger-up":
        tl.from(children, { y: 60, opacity: 0, stagger: 0.15, duration: 0.8, ease: "power3.out" });
        break;
      case "clip-reveal":
        tl.from(children, { clipPath: "inset(100% 0 0 0)", opacity: 0, stagger: 0.15, duration: 1.2, ease: "power4.inOut" });
        break;

      case "text-scramble":
        children.forEach((el, i) => {
          const finalText = el.textContent;
          const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%&*";
          el.style.opacity = 0;
          tl.to(el, {
            opacity: 1,
            duration: 1.2,
            delay: i * 0.15,
            ease: "none",
            onStart: function () { el.style.opacity = 1; },
            onUpdate: function () {
              const progress = this.progress();
              let result = "";
              for (let j = 0; j < finalText.length; j++) {
                result += progress * finalText.length > j
                  ? finalText[j]
                  : chars[Math.floor(Math.random() * chars.length)];
              }
              el.textContent = result;
            },
            onReverseComplete: function () {
              el.textContent = finalText;
              el.style.opacity = 0;
            },
          }, i * 0.15);
        });
        break;

      case "split-reveal":
        const inner = section.querySelector(".section-inner");
        if (inner) {
          tl.fromTo(inner,
            { clipPath: "inset(0 50% 0 50%)" },
            { clipPath: "inset(0 0% 0 0%)", duration: 1.4, ease: "power4.inOut" }
          );
          tl.from(children, { opacity: 0, y: 20, stagger: 0.1, duration: 0.6 }, "-=0.6");
        }
        break;

      case "horizontal-scroll":
        // Handled separately
        break;
    }

    // Scroll-driven play/reverse
    let isVisible = false;
    ScrollTrigger.create({
      trigger: scrollContainer,
      start: "top top",
      end: "bottom bottom",
      scrub: true,
      onUpdate: (self) => {
        const p = self.progress;
        if (p >= enter && p <= leave) {
          if (!isVisible) {
            isVisible = true;
            section.classList.add("visible");
            tl.play();
          }
        } else {
          if (isVisible && !persist) {
            isVisible = false;
            section.classList.remove("visible");
            tl.reverse();
          }
        }
      },
    });
  });
}

// ===========================
// 7. COUNTER ANIMATIONS
// ===========================
function initCounters() {
  document.querySelectorAll(".stat-number").forEach((el) => {
    const target = parseFloat(el.dataset.value);
    const decimals = parseInt(el.dataset.decimals || "0");
    el._counter = { val: 0 };

    ScrollTrigger.create({
      trigger: scrollContainer,
      start: "top top",
      end: "bottom bottom",
      scrub: true,
      onUpdate: (self) => {
        const section = el.closest(".scroll-section");
        if (section && section.classList.contains("visible")) {
          gsap.to(el._counter, {
            val: target,
            duration: 1.5,
            ease: "power1.out",
            onUpdate: () => {
              el.textContent = decimals > 0
                ? el._counter.val.toFixed(decimals)
                : Math.round(el._counter.val);
            },
          });
        }
      },
    });
  });
}

// ===========================
// 8. MARQUEE
// ===========================
function initMarquee() {
  document.querySelectorAll(".marquee-wrap").forEach((el) => {
    const speed = parseFloat(el.dataset.scrollSpeed) || -25;
    const text = el.querySelector(".marquee-text");

    gsap.to(text, {
      xPercent: speed,
      ease: "none",
      scrollTrigger: {
        trigger: scrollContainer,
        start: "top top",
        end: "bottom bottom",
        scrub: true,
      },
    });

    // Fade marquee in/out
    ScrollTrigger.create({
      trigger: scrollContainer,
      start: "top top",
      end: "bottom bottom",
      scrub: true,
      onUpdate: (self) => {
        const p = self.progress;
        if (p > 0.08 && p < 0.85) {
          el.style.opacity = Math.min(1, (p - 0.08) / 0.05);
        } else {
          el.style.opacity = 0;
        }
      },
    });
  });
}

// ===========================
// 9. DARK OVERLAY
// ===========================
function initDarkOverlay() {
  const enter = 0.42;
  const leave = 0.58;
  const fadeRange = 0.04;

  ScrollTrigger.create({
    trigger: scrollContainer,
    start: "top top",
    end: "bottom bottom",
    scrub: true,
    onUpdate: (self) => {
      const p = self.progress;
      let opacity = 0;
      if (p >= enter - fadeRange && p <= enter)
        opacity = (p - (enter - fadeRange)) / fadeRange;
      else if (p > enter && p < leave) opacity = 0.9;
      else if (p >= leave && p <= leave + fadeRange)
        opacity = 0.9 * (1 - (p - leave) / fadeRange);
      darkOverlay.style.opacity = opacity;
    },
  });
}

// ===========================
// 10. HORIZONTAL SCROLL
// ===========================
function initHorizontalScroll() {
  document.querySelectorAll("[data-animation='horizontal-scroll']").forEach((section) => {
    const track = section.querySelector(".horizontal-track");
    if (!track) return;

    const enter = parseFloat(section.dataset.enter) / 100;
    const leave = parseFloat(section.dataset.leave) / 100;

    ScrollTrigger.create({
      trigger: scrollContainer,
      start: "top top",
      end: "bottom bottom",
      scrub: 1,
      onUpdate: (self) => {
        const p = self.progress;
        if (p >= enter && p <= leave) {
          section.classList.add("visible");
          const localProgress = (p - enter) / (leave - enter);
          const maxX = track.scrollWidth - window.innerWidth;
          track.style.transform = `translateX(${-localProgress * maxX}px)`;
        } else {
          section.classList.remove("visible");
        }
      },
    });
  });
}

// ===========================
// 11. SVG PATH DRAW
// ===========================
function initSVGDraw() {
  document.querySelectorAll("[data-svg-draw]").forEach((svg) => {
    const paths = svg.querySelectorAll("path");
    paths.forEach((path) => {
      const length = path.getTotalLength();
      path.style.strokeDasharray = length;
      path.style.strokeDashoffset = length;
    });

    ScrollTrigger.create({
      trigger: scrollContainer,
      start: "top top",
      end: "bottom bottom",
      scrub: true,
      onUpdate: (self) => {
        const p = self.progress;
        // Draw between 60-90% scroll
        if (p > 0.6 && p < 0.95) {
          svg.style.opacity = 1;
          const drawProgress = (p - 0.6) / 0.3;
          paths.forEach((path) => {
            const length = path.getTotalLength();
            path.style.strokeDashoffset = length * (1 - drawProgress);
          });
        } else {
          svg.style.opacity = 0;
        }
      },
    });
  });
}

// ===========================
// 12. VELOCITY EFFECTS
// ===========================
function initVelocityEffects() {
  let currentVelocity = 0;
  lenis.on("scroll", (e) => {
    currentVelocity = e.velocity;
  });

  document.querySelectorAll("[data-velocity-skew]").forEach((el) => {
    gsap.ticker.add(() => {
      const skew = Math.min(Math.max(currentVelocity * 0.2, -6), 6);
      gsap.to(el, { skewY: skew, duration: 0.4, ease: "power2.out" });
    });
  });
}

// ===========================
// 13. PROGRESS BAR
// ===========================
function initProgressBar() {
  document.querySelectorAll("[data-progress-bar]").forEach((bar) => {
    gsap.to(bar, {
      scaleX: 1,
      ease: "none",
      scrollTrigger: {
        trigger: scrollContainer,
        start: "top top",
        end: "bottom bottom",
        scrub: true,
      },
    });
  });
}

// ===========================
// INIT
// ===========================
async function init() {
  // Stop scroll during load
  lenis.stop();

  await preloadFrames();

  // Hide loader
  loader.classList.add("hidden");
  setTimeout(() => {
    loader.style.display = "none";
  }, 600);

  // Start scroll
  lenis.start();

  // Hero word animation
  gsap.from(".hero-heading span", {
    y: 80,
    opacity: 0,
    stagger: 0.15,
    duration: 1.2,
    ease: "power3.out",
    delay: 0.3,
  });
  gsap.from(".hero-tagline", {
    y: 30,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out",
    delay: 0.7,
  });
  gsap.from(".section-label", {
    y: 20,
    opacity: 0,
    duration: 0.6,
    ease: "power3.out",
    delay: 0.5,
  });

  // Init all systems
  initFrameScroll();
  initHeroTransition();
  setupSections();
  initCounters();
  initMarquee();
  initDarkOverlay();
  initHorizontalScroll();
  initSVGDraw();
  initVelocityEffects();
  initProgressBar();
}

init();
