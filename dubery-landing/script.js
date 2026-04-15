/* ============================================================
   DUBERY LANDING PAGE — script.js
   Dynamic caption loading · Modal · Picker · Form submit
   ============================================================ */

'use strict';

/* ── Config ───────────────────────────────────────────────── */
// Set this after Google Apps Script is deployed
const FORM_ENDPOINT = 'https://script.google.com/macros/s/AKfycbxFD6z-PR8tcQhHpH-UulU-3Nk8OpqWgWeyD-J0unJser7Cptd4tP-3D6iM8W0eOoWCtg/exec';

/* ── Product image map ────────────────────────────────────── */
// variantIdx maps to VARIANTS array index for auto-populating the order picker
const PRODUCT_IMAGE_MAP = [
  { keys: ['outback black'],                   img: 'assets/cards/outback-black-card-shot.jpg', label: 'OUTBACK BLACK',           variantIdx: 0, desc: 'The everyday carry. Matte black frame, polarized lens -- clean and no-nonsense.' },
  { keys: ['outback blue'],                    img: 'assets/cards/outback-blue-card-shot.jpg',  label: 'OUTBACK BLUE',            variantIdx: 1, desc: 'Cool blue polarized lens, lightweight frame. Clean enough for work, tough enough for the road.' },
  { keys: ['outback red'],                     img: 'assets/cards/outback-red-card-shot.jpg',   label: 'OUTBACK RED',             variantIdx: 2, desc: 'Red polarized lens, black frame. The pair that gets noticed first in any lineup.' },
  { keys: ['outback green'],                   img: 'assets/cards/outback-green-card-shot.jpg', label: 'OUTBACK GREEN',           variantIdx: 3, desc: 'Military green lens, polarized. Understated but never overlooked. Pairs with denim, camo, or a plain white tee.' },
  { keys: ['outback series', 'outback'],       img: 'assets/cards/outback-black-card-shot.jpg', label: 'OUTBACK SERIES',          variantIdx: 0, desc: 'Four colorways, one frame. Polarized lens, lightweight build -- pick your color.' },
  { keys: ['bandits matte black', 'bandits matte'], img: 'assets/cards/bandits-matte-black-card-shot.jpg', label: 'BANDITS MATTE BLACK', variantIdx: 6, desc: 'Stealth mode. Matte black frame, polarized lens. Clean and low-key.' },
  { keys: ['bandits glossy black', 'bandits black'], img: 'assets/cards/bandits-glossy-black-card-shot.jpg', label: 'BANDITS BLACK', variantIdx: 7, desc: 'Glossy black finish, polarized lens. From meetings to merienda.' },
  { keys: ['bandits green'],                   img: 'assets/cards/bandits-green-card-shot.jpg', label: 'BANDITS GREEN',           variantIdx: 8, desc: 'The one your tropa notices first. Green two-tone frame with polarized lens for real UV protection.<br>Lightweight enough to forget you are wearing them.' },
  { keys: ['bandits blue'],                    img: 'assets/cards/bandits-blue-card-shot.jpg',  label: 'BANDITS BLUE',            variantIdx: 9, desc: 'Cool blue tint, polarized lens. Clean and easy to wear.' },
  { keys: ['bandits tortoise'],                img: 'assets/cards/bandits-tortoise-card-shot.jpg', label: 'BANDITS TORTOISE',     variantIdx: 10, desc: 'Classic tortoise shell, polarized lens. Timeless from Divisoria to BGC.' },
  { keys: ['rasta red'],                       img: 'assets/cards/rasta-red-card-shot.jpg',     label: 'RASTA RED',               variantIdx: 4, desc: 'Red is not loud when you wear it right. Polarized lens, lightweight frame, all-day comfort.' },
  { keys: ['rasta brown'],                     img: 'assets/cards/rasta-brown-card-shot.jpg',   label: 'RASTA BROWN',             variantIdx: 5, desc: 'The neutral that is not boring. Warm brown tint, polarized clarity, goes with everything.' },
  { keys: ['rasta series', 'rasta'],           img: 'assets/cards/rasta-red-card-shot.jpg',     label: 'RASTA SERIES',            variantIdx: 4, desc: 'Reggae-inspired colorways, polarized lens. Pick your vibe.' },
  { keys: ['classic black', 'classic dark', 'classic'], img: 'assets/cards/bandits-glossy-black-card-shot.jpg', label: 'SUNGLASSES', variantIdx: 7, desc: 'Polarized lens, clean build. Looks good everywhere -- from Divisoria to BGC.' },
  { keys: ['bundle', 'mixed'],                 img: 'assets/bundle.jpg',                            label: 'BUNDLE',              variantIdx: null, desc: 'Mix and match. Two pairs, one deal -- same-day delivery, COD.' },
];

const PRODUCT_DEFAULT = { img: 'assets/variants/outback-black.jpg', label: 'DUBERY POLARIZED SUNGLASSES' };

function resolveProductImage(productRef) {
  if (!productRef) return PRODUCT_DEFAULT;
  const ref = productRef.toLowerCase();
  for (const entry of PRODUCT_IMAGE_MAP) {
    if (entry.keys.some(k => ref.includes(k))) {
      return { img: entry.img, label: entry.label, desc: entry.desc, variantIdx: entry.variantIdx };
    }
  }
  return PRODUCT_DEFAULT;
}

function resolveMultiProducts(productRef) {
  if (!productRef) return [PRODUCT_DEFAULT];
  const parts = productRef.split(',').map(s => s.trim()).filter(Boolean);
  if (parts.length <= 1) return null; // single product — use normal flow
  const resolved = parts.map(p => resolveProductImage(p)).filter(
    (v, i, arr) => arr.findIndex(x => x.img === v.img) === i // dedupe
  );
  return resolved.length > 1 ? resolved : null;
}

function renderProductCarousel(products) {
  const card = document.querySelector('.hero-product-card');
  if (!card) return;
  card.innerHTML = `
    <div class="product-carousel">
      <div class="product-carousel-track" id="carousel-track">
        ${products.map((p, i) => `
          <div class="carousel-slide${i === 0 ? ' active' : ''}">
            <img src="${p.img}" alt="${p.label}" loading="lazy" style="cursor:zoom-in" />
            <span class="carousel-label">${p.label}</span>
            <p class="carousel-slide-desc">${p.desc || ''}</p>
          </div>
        `).join('')}
      </div>
      <div class="carousel-dots">
        ${products.map((_, i) => `<button class="carousel-dot${i === 0 ? ' active' : ''}" data-index="${i}" aria-label="Product ${i+1}"></button>`).join('')}
      </div>
    </div>
  `;

  // Tap to preview each slide image
  card.querySelectorAll('.carousel-slide img').forEach((img, i) => {
    img.addEventListener('click', () => {
      const items = products.map(p => ({ src: p.img, alt: p.label, desc: p.desc }));
      openImgPreview(img.src, products[i].label, products[i].desc, items, i);
    });
  });

  initCarousel(card, products);
}

function prePopulatePicker(products) {
  // Clear existing rows and rebuild with featured products pre-selected
  pickerRows.innerHTML = '';
  products.forEach(p => {
    if (p.variantIdx === null || p.variantIdx === undefined) return;
    const row = addPickerRow();
    const select = row.querySelector('.picker-select-wrap');
    const qtyDisplay = row.querySelector('.qty-display');
    const thumbImg = row.querySelector('.picker-thumb img');
    select.value = p.variantIdx;
    qtyDisplay.textContent = '1';
    const variant = VARIANTS[p.variantIdx];
    thumbImg.src = variant.img;
    thumbImg.alt = variant.name;
    thumbImg.classList.add('variant-selected');
    thumbImg.onload = () => thumbImg.classList.add('loaded');
  });
  addPickerRow(); // blank trailing row
  updateSummary();
}

function initCarousel(card, products) {
  const count   = products.length;
  const track   = card.querySelector('#carousel-track');
  const dots    = card.querySelectorAll('.carousel-dot');
  let current   = 0;
  let startX    = 0;

  function goTo(idx) {
    current = (idx + count) % count;
    track.style.transform = `translateX(-${current * 100}%)`;
    dots.forEach((d, i) => d.classList.toggle('active', i === current));
  }

  dots.forEach(d => d.addEventListener('click', () => goTo(+d.dataset.index)));

  track.addEventListener('touchstart', e => { startX = e.touches[0].clientX; }, { passive: true });
  track.addEventListener('touchend', e => {
    const diff = startX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 40) goTo(current + (diff > 0 ? 1 : -1));
  });
}

/* ── Variant data ─────────────────────────────────────────── */
const VARIANTS = [
  { name: 'Outback – Black',        img: 'assets/variants/outback-black.jpg', gallery: ['assets/variants/outback-black.jpg', 'assets/variants/outback-black/gallery-1.jpg', 'assets/variants/outback-black/gallery-2.jpg', 'assets/variants/outback-black/gallery-3.jpg', 'assets/variants/outback-black/gallery-4.jpg'] },
  { name: 'Outback – Blue',         img: 'assets/variants/outback-blue.jpg', gallery: ['assets/variants/outback-blue.jpg', 'assets/variants/outback-blue/gallery-1.jpg', 'assets/variants/outback-blue/gallery-2.jpg', 'assets/variants/outback-blue/gallery-3.jpg', 'assets/variants/outback-blue/gallery-4.jpg', 'assets/variants/outback-blue/gallery-5.jpg'] },
  { name: 'Outback – Red',          img: 'assets/variants/outback-red.jpg', gallery: ['assets/variants/outback-red.jpg', 'assets/variants/outback-red/gallery-1.jpg', 'assets/variants/outback-red/gallery-2.jpg', 'assets/variants/outback-red/gallery-3.jpg', 'assets/variants/outback-red/gallery-4.jpg', 'assets/variants/outback-red/gallery-5.jpg'] },
  { name: 'Outback – Green',        img: 'assets/variants/outback-green.jpg', gallery: ['assets/variants/outback-green.jpg', 'assets/variants/outback-green/gallery-1.jpg', 'assets/variants/outback-green/gallery-2.jpg', 'assets/variants/outback-green/gallery-3.jpg', 'assets/variants/outback-green/gallery-4.jpg'] },
  { name: 'Rasta – Red',            img: 'assets/variants/rasta-red.jpg', gallery: ['assets/variants/rasta-red.jpg', 'assets/variants/rasta-red/gallery-1.jpg', 'assets/variants/rasta-red/gallery-2.jpg', 'assets/variants/rasta-red/gallery-3.jpg', 'assets/variants/rasta-red/gallery-4.jpg', 'assets/variants/rasta-red/gallery-5.jpg'] },
  { name: 'Rasta – Brown',          img: 'assets/variants/rasta-brown.jpg', gallery: ['assets/variants/rasta-brown.jpg', 'assets/variants/rasta-brown/gallery-1.jpg', 'assets/variants/rasta-brown/gallery-2.jpg', 'assets/variants/rasta-brown/gallery-3.jpg', 'assets/variants/rasta-brown/gallery-4.jpg', 'assets/variants/rasta-brown/gallery-5.jpg'] },
  { name: 'Bandits – Matte Black',  img: 'assets/variants/bandits-matte-black.jpg', gallery: ['assets/variants/bandits-matte-black.jpg', 'assets/variants/bandits-matte-black/gallery-1.jpg', 'assets/variants/bandits-matte-black/gallery-2.jpg', 'assets/variants/bandits-matte-black/gallery-3.jpg', 'assets/variants/bandits-matte-black/gallery-4.jpg', 'assets/variants/bandits-matte-black/gallery-5.jpg'] },
  { name: 'Bandits – Black',        img: 'assets/variants/bandits-glossy-black.jpg', gallery: ['assets/variants/bandits-glossy-black.jpg', 'assets/variants/bandits-glossy-black/gallery-1.jpg', 'assets/variants/bandits-glossy-black/gallery-2.jpg', 'assets/variants/bandits-glossy-black/gallery-3.jpg', 'assets/variants/bandits-glossy-black/gallery-4.jpg'] },
  { name: 'Bandits – Green',        img: 'assets/variants/bandits-green.jpg', gallery: ['assets/variants/bandits-green.jpg', 'assets/variants/bandits-green/gallery-1.jpg', 'assets/variants/bandits-green/gallery-2.jpg', 'assets/variants/bandits-green/gallery-3.jpg', 'assets/variants/bandits-green/gallery-4.jpg', 'assets/variants/bandits-green/gallery-5.jpg'] },
  { name: 'Bandits – Blue',         img: 'assets/variants/bandits-blue.jpg', gallery: ['assets/variants/bandits-blue.jpg', 'assets/variants/bandits-blue/gallery-1.jpg', 'assets/variants/bandits-blue/gallery-2.jpg', 'assets/variants/bandits-blue/gallery-3.jpg', 'assets/variants/bandits-blue/gallery-4.jpg'] },
  { name: 'Bandits – Tortoise',     img: 'assets/variants/bandits-tortoise.jpg', gallery: ['assets/variants/bandits-tortoise.jpg', 'assets/variants/bandits-tortoise/gallery-1.jpg', 'assets/variants/bandits-tortoise/gallery-2.jpg', 'assets/variants/bandits-tortoise/gallery-3.jpg', 'assets/variants/bandits-tortoise/gallery-4.jpg', 'assets/variants/bandits-tortoise/gallery-5.jpg'] },
];

/* ── DOM refs ─────────────────────────────────────────────── */
const heroBg       = document.getElementById('hero-bg');
const heroHeadline = document.getElementById('hero-headline');
const heroSub      = document.getElementById('hero-sub');
const modal        = document.getElementById('order-modal');
const backdrop     = document.getElementById('modal-backdrop');
const closeBtn     = document.getElementById('modal-close-btn');
const openBtns     = document.querySelectorAll('.open-modal-btn');
const form         = document.getElementById('order-form');
const confirmation = document.getElementById('confirmation');
const pickerRows   = document.getElementById('picker-rows');
const autofillBtn  = document.getElementById('btn-autofill');

const summaryEmpty = document.getElementById('summary-empty');
const summaryLines = document.getElementById('summary-lines');
const summaryTotal = document.getElementById('summary-total');
const totalCount   = document.getElementById('total-count');
const summaryNudge    = document.getElementById('summary-nudge');
const summaryDelivery = document.getElementById('summary-delivery');
const deliveryFee     = document.getElementById('delivery-fee');
const summaryCod      = document.getElementById('summary-cod');
const summaryAmount     = document.getElementById('summary-amount');
const totalAmount       = document.getElementById('total-amount');
const summaryDivider    = document.getElementById('summary-divider');
const summaryGrandTotal = document.getElementById('summary-grand-total');
const grandTotal        = document.getElementById('grand-total');

function calcPrice(pairs) {
  if (pairs <= 0) return 0;
  if (pairs === 1) return 599;
  const bundles = Math.floor(pairs / 2);
  const singles = pairs % 2;
  return bundles * 1099 + singles * 599;
}
const submitBtn    = document.getElementById('submit-btn');
const expressBtn   = document.getElementById('submit-express-btn');
let isExpressOrder = false;

if (expressBtn) {
  expressBtn.addEventListener('click', (e) => {
    e.preventDefault();
    isExpressOrder = true;
    form.requestSubmit();
  });
}

/* ── Product card image preview ───────────────────────────── */
const productPhoto = document.getElementById('product-photo');
if (productPhoto) {
  productPhoto.style.cursor = 'zoom-in';
  productPhoto.addEventListener('click', () => {
    openImgPreview(productPhoto.src, productPhoto.alt || 'Dubery Polarized');
  });
}

/* ── State ────────────────────────────────────────────────── */
let activeCaptionId = null;
let featuredVariantIndices = [];

/* ── Google Maps Places Autocomplete ─────────────────────── */
/* Google Places removed -- using browser native autocomplete */

/* Toggle filled class on form inputs for dark mode styling */
document.querySelectorAll('.form-input').forEach(input => {
  function checkFilled() { input.classList.toggle('filled', input.value.trim().length > 0); }
  input.addEventListener('input', checkFilled);
  input.addEventListener('change', checkFilled);
  checkFilled();
});

/* ── Accent Color Extraction ──────────────────────────────── */
function rgbToHsl(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0, s = 0, l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  return [h, s, l];
}

function hslToHex(h, s, l) {
  const hue2rgb = (p, q, t) => {
    if (t < 0) t += 1; if (t > 1) t -= 1;
    if (t < 1/6) return p + (q - p) * 6 * t;
    if (t < 1/2) return q;
    if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
    return p;
  };
  let r, g, b;
  if (s === 0) { r = g = b = l; }
  else {
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h + 1/3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1/3);
  }
  const toHex = x => Math.round(x * 255).toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function extractAndApplyAccent(imgUrl) {
  const img = new Image();
  img.onload = () => {
    try {
      const W = 80, H = 80;
      const canvas = document.createElement('canvas');
      canvas.width = W; canvas.height = H;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, W, H);
      const data = ctx.getImageData(0, 0, W, H).data;

      let bestH = 0, bestS = 0, bestScore = 0;
      for (let i = 0; i < data.length; i += 4) {
        const [h, s, l] = rgbToHsl(data[i], data[i+1], data[i+2]);
        if (s < 0.15 || l < 0.05 || l > 0.95) continue;
        const score = s * (1 - Math.abs(l - 0.5) * 1.2);
        if (score > bestScore) { bestScore = score; bestH = h; bestS = s; }
      }

      // Dynamic accent disabled -- using fixed green (#16a34a)
      // if (bestScore > 0) applyTheme(bestH, bestS);
    } catch(e) {
      console.warn('Accent extraction failed:', e);
    }
  };
  img.onerror = () => console.warn('Hero image failed to load for accent extraction:', imgUrl);
  img.src = imgUrl;
}

function applyTheme(h, s) {
  const sc = Math.min(s, 0.88);
  const hDeg = Math.round(h * 360);
  const sPct = Math.round(sc * 100);
  console.log(`[DuberyTheme] hue=${hDeg} sat=${sPct}% → bg=${hslToHex(h, 0.20, 0.07)} accent=${hslToHex(h, sc, 0.48)}`);

  document.documentElement.style.setProperty('--accent',        hslToHex(h, sc, 0.48));
  document.documentElement.style.setProperty('--accent-hover',  hslToHex(h, sc, 0.56));
  document.documentElement.style.setProperty('--accent-active', hslToHex(h, sc, 0.38));
  document.documentElement.style.setProperty('--accent-glow',   `hsla(${hDeg},${sPct}%,48%,0.2)`);
  // Accent tints the surface cards slightly
  document.documentElement.style.setProperty('--surface',        `hsla(${hDeg},30%,98%,0.60)`);
  document.documentElement.style.setProperty('--surface-raised', `hsla(${hDeg},25%,100%,0.75)`);
  document.documentElement.style.setProperty('--surface-border', `hsla(${hDeg},20%,70%,0.25)`);
}

/* ── Dynamic Caption Loading ──────────────────────────────── */
function setPageBg(imgUrl) {
  const el = document.getElementById('page-bg');
  if (el) el.style.backgroundImage = `url('${imgUrl}')`;
}

function applyCaption(caption) {
  activeCaptionId = caption.id;

  // Determine featured variant indices for dropdown reordering
  featuredVariantIndices = [];
  if (caption.product_ref) {
    const refs = caption.product_ref.split(',').map(s => s.trim().toLowerCase());
    refs.forEach(ref => {
      const idx = VARIANTS.findIndex(v => v.name.toLowerCase().includes(ref) || ref.includes(v.name.toLowerCase().replace(/\s*–\s*/g, ' ').trim()));
      if (idx >= 0 && !featuredVariantIndices.includes(idx)) featuredVariantIndices.push(idx);
    });
  }

  // Swap hero image + extract accent + set blurred page bg
  const imgUrl = `assets/ads/dubery_${caption.id}.jpg`;
  heroBg.style.backgroundImage = `url('${imgUrl}')`;
  setPageBg(imgUrl);
  extractAndApplyAccent(imgUrl);

  // Swap product card image + label (carousel for multi-product)
  const multiProducts = resolveMultiProducts(caption.product_ref);
  if (multiProducts) {
    renderProductCarousel(multiProducts);
    // prePopulatePicker(multiProducts); -- disabled to avoid price shock
  } else {
    const productPhoto = document.getElementById('product-photo');
    const productName  = document.getElementById('product-name');
    const resolved = caption.card_image
      ? { img: `assets/${caption.card_image}`, label: resolveProductImage(caption.product_ref).label }
      : resolveProductImage(caption.product_ref);
    if (productPhoto) productPhoto.src = resolved.img;
    if (productName)  productName.textContent = resolved.label;
    const productDesc = document.getElementById('product-desc');
    if (productDesc) productDesc.innerHTML = resolved.desc || '';
    // prePopulatePicker([resolved]); -- disabled to avoid price shock
  }

  // Swap headline + sub (elements may not exist if removed from template)
  if (caption.headline && heroHeadline) heroHeadline.textContent = caption.headline;
  if (caption.vibe && heroSub) heroSub.textContent = `${caption.vibe} · Polarized Sunglasses`;
}


/* ── Pricing cards clickable ──────────────────────────────── */
document.querySelectorAll('.pricing-card').forEach(card => {
  card.addEventListener('click', (e) => {
    if (e.target.closest('.btn')) return; // let button handle itself
    openModal();
  });
});

/* ── Modal ────────────────────────────────────────────────── */
function openModal() {
  modal.classList.add('active');
  backdrop.classList.add('active');
  backdrop.removeAttribute('aria-hidden');
  document.body.classList.add('modal-open');
  modal.setAttribute('aria-hidden', 'false');
  const firstInput = modal.querySelector('input, textarea, select, button');
  if (firstInput) requestAnimationFrame(() => firstInput.focus());
}

function closeModal() {
  modal.classList.remove('active');
  backdrop.classList.remove('active');
  backdrop.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('modal-open');
  modal.setAttribute('aria-hidden', 'true');
}

openBtns.forEach(btn => btn.addEventListener('click', openModal));
closeBtn.addEventListener('click', closeModal);
backdrop.addEventListener('click', closeModal);

document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && modal.classList.contains('active')) closeModal();
  if (e.key === 'Escape') closeImgPreview();
});

const imgPreviewOverlay = document.getElementById('img-preview-overlay');
function closeImgPreview() {
  imgPreviewOverlay.classList.remove('active');
  imgPreviewOverlay.setAttribute('aria-hidden', 'true');
}
let previewItems = [];
let previewIndex = 0;

function openImgPreview(src, alt, desc, items, idx, showActions) {
  if (items) {
    previewItems = items;
    previewIndex = idx || 0;
  } else {
    previewItems = [{ src, alt, desc }];
    previewIndex = 0;
  }
  const actions = document.querySelector('.img-preview-actions');
  if (actions) actions.style.display = showActions === false ? 'none' : 'flex';
  imgPreviewOverlay.classList.toggle('has-multiple', previewItems.length > 1);
  showPreviewSlide();
  imgPreviewOverlay.classList.add('active');
  imgPreviewOverlay.setAttribute('aria-hidden', 'false');
}

function showPreviewSlide() {
  const item = previewItems[previewIndex];
  const previewImg = document.getElementById('img-preview-img');
  const previewInfo = document.getElementById('img-preview-info');
  previewImg.src = item.src;
  previewImg.alt = item.alt || '';
  if (previewInfo) {
    const counter = previewItems.length > 1 ? `<span class="img-preview-counter">${previewIndex + 1} / ${previewItems.length}</span>` : '';
    previewInfo.innerHTML = (item.desc ? `<strong>${item.alt}</strong><p>${item.desc}</p>` : `<strong>${item.alt}</strong>`) + counter;
  }
}

(function() {
  let startX = 0;
  imgPreviewOverlay.addEventListener('touchstart', e => { startX = e.touches[0].clientX; }, { passive: true });
  imgPreviewOverlay.addEventListener('touchend', e => {
    const diff = startX - e.changedTouches[0].clientX;
    if (previewItems.length <= 1) { if (Math.abs(diff) < 40) closeImgPreview(); return; }
    if (Math.abs(diff) > 40) {
      previewIndex = (previewIndex + (diff > 0 ? 1 : -1) + previewItems.length) % previewItems.length;
      showPreviewSlide();
    } else {
      closeImgPreview();
    }
  });
  imgPreviewOverlay.addEventListener('click', e => {
    if (e.target === imgPreviewOverlay) closeImgPreview();
    if (e.target.closest('.img-preview-btn.open-modal-btn')) { closeImgPreview(); openModal(); }
  });
  document.addEventListener('keydown', e => {
    if (!imgPreviewOverlay.classList.contains('active')) return;
    if (e.key === 'Escape') { closeImgPreview(); return; }
    if (previewItems.length <= 1) return;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      previewIndex = (previewIndex + 1) % previewItems.length;
      showPreviewSlide();
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      previewIndex = (previewIndex - 1 + previewItems.length) % previewItems.length;
      showPreviewSlide();
    }
  });
})();

modal.addEventListener('keydown', e => {
  if (e.key !== 'Tab') return;
  const focusable = Array.from(modal.querySelectorAll(
    'button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
  )).filter(el => !el.disabled && el.offsetParent !== null);
  if (!focusable.length) return;
  const first = focusable[0];
  const last  = focusable[focusable.length - 1];
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault(); last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault(); first.focus();
  }
});

/* ── Product Picker ───────────────────────────────────────── */
function buildSelect() {
  const wrapper = document.createElement('div');
  wrapper.className = 'picker-select-wrap';

  const trigger = document.createElement('button');
  trigger.type = 'button';
  trigger.className = 'picker-select';
  trigger.innerHTML = '<span class="picker-select-text">Select a variant...</span>';
  trigger.dataset.value = '';

  const dropdown = document.createElement('div');
  dropdown.className = 'picker-dropdown';

  // Dropdown items built dynamically on open via rebuildDropdown()

  function getSelectedIndices() {
    const selected = new Set();
    pickerRows.querySelectorAll('.picker-select-wrap').forEach(sw => {
      const val = sw.value;
      if (val !== '' && sw !== wrapper) selected.add(parseInt(val, 10));
    });
    return selected;
  }

  function rebuildDropdown() {
    dropdown.innerHTML = '';
    const order = [...featuredVariantIndices];
    VARIANTS.forEach((_, i) => { if (!order.includes(i)) order.push(i); });
    const hasSelection = trigger.dataset.value !== '';
    const taken = getSelectedIndices();

    order.forEach(i => {
      if (taken.has(i)) return;
      const v = VARIANTS[i];
      const item = document.createElement('div');
      item.className = 'picker-dropdown-item' + (featuredVariantIndices.includes(i) ? ' featured' : '');
      item.dataset.value = i;
      item.innerHTML = hasSelection ? `<span>${v.name}</span>` : `<img src="${v.img}" alt="${v.name}" /><span>${v.name}</span>`;
      item.addEventListener('click', () => {
        trigger.innerHTML = `<span class="picker-select-text">${v.name}</span>`;
        trigger.dataset.value = i;
        dropdown.classList.remove('open');
        wrapper.dispatchEvent(new Event('change'));
      });
      dropdown.appendChild(item);
    });
  }

  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    rebuildDropdown();
    document.querySelectorAll('.picker-dropdown.open').forEach(d => { if (d !== dropdown) d.classList.remove('open'); });
    dropdown.classList.toggle('open');
  });

  document.addEventListener('click', () => { dropdown.classList.remove('open'); });

  // Mimic select API
  Object.defineProperty(wrapper, 'value', {
    get() { return trigger.dataset.value; },
    set(v) {
      trigger.dataset.value = v;
      if (v !== '' && VARIANTS[v]) {
        const vr = VARIANTS[v];
        trigger.innerHTML = `<span class="picker-select-text">${vr.name}</span>`;
        dropdown.classList.add('compact');
      }
    }
  });

  wrapper.appendChild(trigger);
  wrapper.appendChild(dropdown);
  return wrapper;
}

function addPickerRow() {
  const row = document.createElement('div');
  row.className = 'picker-row';

  const thumb = document.createElement('div');
  thumb.className = 'picker-thumb';
  const thumbImg = document.createElement('img');
  thumbImg.alt = 'Dubery';
  thumbImg.src = 'assets/logo-new-2.png';
  thumbImg.classList.add('loaded');
  thumb.style.cursor = 'pointer';
  thumb.addEventListener('click', () => {
    if (!thumbImg.src || !thumbImg.classList.contains('loaded')) return;
    const selWrap = row.querySelector('.picker-select-wrap');
    const varIdx = selWrap ? parseInt(selWrap.value, 10) : NaN;
    const variant = !isNaN(varIdx) ? VARIANTS[varIdx] : null;
    if (variant && variant.gallery && variant.gallery.length > 1) {
      const items = variant.gallery.map(src => ({ src, alt: variant.name, desc: '' }));
      openImgPreview(items[0].src, variant.name, '', items, 0, false);
    } else {
      openImgPreview(thumbImg.src, thumbImg.alt, null, null, null, false);
    }
  });
  thumb.appendChild(thumbImg);

  const select = buildSelect();

  const stepper = document.createElement('div');
  stepper.className = 'stepper';
  stepper.setAttribute('role', 'group');
  stepper.setAttribute('aria-label', 'Quantity');

  const btnMinus = document.createElement('button');
  btnMinus.type = 'button';
  btnMinus.className = 'stepper-btn';
  btnMinus.textContent = '−';
  btnMinus.setAttribute('aria-label', 'Decrease quantity');

  const qtyDisplay = document.createElement('span');
  qtyDisplay.className = 'qty-display';
  qtyDisplay.textContent = '0';
  qtyDisplay.setAttribute('aria-live', 'polite');

  const btnPlus = document.createElement('button');
  btnPlus.type = 'button';
  btnPlus.className = 'stepper-btn';
  btnPlus.textContent = '+';
  btnPlus.setAttribute('aria-label', 'Increase quantity');

  stepper.appendChild(btnMinus);
  stepper.appendChild(qtyDisplay);
  stepper.appendChild(btnPlus);

  row.appendChild(thumb);
  row.appendChild(select);
  row.appendChild(stepper);

  select.addEventListener('change', () => {
    const idx = parseInt(select.value, 10);
    select.querySelector('.picker-dropdown')?.classList.remove('open');
    if (isNaN(idx)) return;
    const variant = VARIANTS[idx];
    thumbImg.src = variant.img + '?v=' + Date.now();
    thumbImg.alt = variant.name;
    thumbImg.classList.remove('loaded');
    thumbImg.classList.add('variant-selected');
    thumbImg.onload = () => thumbImg.classList.add('loaded');
    if (parseInt(qtyDisplay.textContent, 10) === 0) qtyDisplay.textContent = '1';
    const rows = pickerRows.querySelectorAll('.picker-row');
    if (row === rows[rows.length - 1]) addPickerRow();
    updateSummary();
    clearPickerError();
  });

  btnMinus.addEventListener('click', () => {
    let qty = parseInt(qtyDisplay.textContent, 10);
    qty = Math.max(0, qty - 1);
    qtyDisplay.textContent = qty;
    const rows = pickerRows.querySelectorAll('.picker-row');
    const isLast = row === rows[rows.length - 1];
    if (qty === 0 && !isLast && select.value !== '') row.remove();
    updateSummary();
  });

  btnPlus.addEventListener('click', () => {
    if (select.value === '') return;
    qtyDisplay.textContent = parseInt(qtyDisplay.textContent, 10) + 1;
    updateSummary();
  });

  pickerRows.appendChild(row);
  return row;
}

/* ── Order Summary ────────────────────────────────────────── */
function updateSummary() {
  const rows = pickerRows.querySelectorAll('.picker-row');
  const items = [];
  rows.forEach(row => {
    const sel = row.querySelector('.picker-select-wrap');
    const qty = parseInt(row.querySelector('.qty-display').textContent, 10);
    if (sel.value !== '' && qty > 0) {
      const variant = VARIANTS[parseInt(sel.value, 10)];
      items.push({ name: variant.name, qty, img: variant.img });
    }
  });

  if (items.length === 0) {
    summaryEmpty.hidden = false;
    summaryLines.hidden = true;
    summaryTotal.hidden = true;
    summaryNudge.hidden = true;
    summaryDelivery.hidden = true;
    summaryCod.hidden = true;
    summaryAmount.hidden = true;
    summaryDivider.hidden = true;
    summaryGrandTotal.hidden = true;
    return;
  }

  summaryEmpty.hidden = true;
  summaryLines.hidden = false;
  summaryTotal.hidden = false;
  summaryLines.innerHTML = '';
  let total = 0;

  items.forEach(item => {
    total += item.qty;
    const li = document.createElement('li');
    li.className = 'summary-line';
    li.innerHTML = `<img class="summary-line-img" src="${item.img}" alt="${item.name}" /><span class="summary-line-name">${item.name}</span><span class="summary-line-qty">x${item.qty}</span>`;
    li.querySelector('.summary-line-img').addEventListener('click', () => openImgPreview(item.img, item.name, null, null, null, false));
    summaryLines.appendChild(li);
  });

  // Freebies line — 1 set per pair ordered
  const incLi = document.createElement('li');
  incLi.className = 'summary-line summary-line-inclusions';
  incLi.innerHTML = `<img class="summary-line-img" src="assets/inclusions.png" alt="Freebies" /><span class="summary-line-name">Freebies</span><span class="summary-line-qty">x${total}</span>`;
  incLi.querySelector('.summary-line-img').addEventListener('click', () => openImgPreview('assets/inclusions.png', 'Freebies', null, null, null, false));
  summaryLines.appendChild(incLi);

  totalCount.textContent = total;
  if (total === 1) {
    summaryNudge.hidden = false;
    summaryNudge.innerHTML = 'Add 1 more pair to avail <strong>FREE delivery!</strong>';
    summaryNudge.className = 'summary-nudge';
  } else if (total >= 2) {
    summaryNudge.hidden = false;
    summaryNudge.innerHTML = '&#127881; Congrats! Your order qualifies for<br><strong>FREE delivery!</strong>';
    summaryNudge.className = 'summary-nudge summary-nudge-success';
  } else {
    summaryNudge.hidden = true;
  }
  const price = calcPrice(total);
  summaryAmount.hidden = false;
  totalAmount.textContent = '₱' + price.toLocaleString();
  summaryDelivery.hidden = false;
  summaryCod.hidden = false;
  summaryDivider.hidden = false;
  summaryGrandTotal.hidden = false;
  grandTotal.textContent = total >= 2 ? '₱' + price.toLocaleString() : '₱' + (price + 99).toLocaleString();
  if (total >= 2) {
    deliveryFee.textContent = 'FREE';
    deliveryFee.classList.add('free');
  } else {
    deliveryFee.textContent = '₱99';
    deliveryFee.classList.remove('free');
  }
}

/* ── Validation helpers ───────────────────────────────────── */
function showError(fieldId, errorId) {
  document.getElementById(fieldId)?.classList.add('error');
  document.getElementById(errorId)?.classList.add('visible');
}

function clearError(fieldId, errorId) {
  document.getElementById(fieldId)?.classList.remove('error');
  document.getElementById(errorId)?.classList.remove('visible');
}

function clearPickerError() {
  document.getElementById('picker-error').classList.remove('visible');
}

['field-name', 'field-phone', 'field-address'].forEach(id => {
  document.getElementById(id)?.addEventListener('input', () => {
    clearError(id, id.replace('field-', '') + '-error');
  });
});

function getSelectedItems() {
  const rows = pickerRows.querySelectorAll('.picker-row');
  const items = [];
  rows.forEach(row => {
    const sel = row.querySelector('.picker-select-wrap');
    const qty = parseInt(row.querySelector('.qty-display').textContent, 10);
    if (sel.value !== '' && qty > 0) {
      items.push({ name: VARIANTS[parseInt(sel.value, 10)].name, qty });
    }
  });
  return items;
}

/* ── Form Submit ──────────────────────────────────────────── */
form.addEventListener('submit', async e => {
  e.preventDefault();

  let valid = true;

  const name = document.getElementById('field-name').value.trim();
  if (!name) { showError('field-name', 'name-error'); valid = false; }
  else { clearError('field-name', 'name-error'); }

  const phone = document.getElementById('field-phone').value.trim();
  if (!phone) { showError('field-phone', 'phone-error'); valid = false; }
  else { clearError('field-phone', 'phone-error'); }

  const address = document.getElementById('field-address').value.trim();
  if (!address) { showError('field-address', 'address-error'); valid = false; }
  else { clearError('field-address', 'address-error'); }

  const items = getSelectedItems();
  if (items.length === 0) {
    document.getElementById('picker-error').classList.add('visible');
    valid = false;
  } else {
    clearPickerError();
  }

  if (!valid) return;

  const notes = document.getElementById('field-notes').value.trim();
  const totalPairs = items.reduce((sum, i) => sum + i.qty, 0);
  const orderTotal = calcPrice(totalPairs);
  const orderDelivery = totalPairs >= 2 ? 0 : 99;
  const orderGrandTotal = orderTotal + orderDelivery;
  const payload = { name, phone, address, items, notes, caption_id: activeCaptionId, grand_total: orderGrandTotal, delivery_fee: orderDelivery, express: isExpressOrder };
  isExpressOrder = false;

  // Submit to Google Apps Script endpoint (if configured)
  if (FORM_ENDPOINT) {
    submitBtn.classList.add('loading');
    submitBtn.textContent = 'Submitting...';

    try {
      const formData = new FormData();
      formData.append('payload', JSON.stringify(payload));
      await fetch(FORM_ENDPOINT, {
        method: 'POST',
        body: formData,
        mode: 'no-cors', // Required for Google Apps Script
      });
    } catch (err) {
      // no-cors means we can't read the response — optimistic success
    }
  }
  // If no endpoint configured: just show confirmation (testing/template mode)

  form.hidden = true;
  confirmation.hidden = false;
  confirmation.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
});


/* ── Init ─────────────────────────────────────────────────── */
function init() {
  addPickerRow();
  modal.setAttribute('aria-hidden', 'true');
  backdrop.setAttribute('aria-hidden', 'true');
  const params = new URLSearchParams(window.location.search);

  // Deep link: ?variant=INDEX&order=1 opens modal with product pre-selected
  const variantParam = params.get('variant');
  if (variantParam !== null) {
    const idx = parseInt(variantParam, 10);
    if (idx >= 0 && idx < VARIANTS.length) {
      const variant = VARIANTS[idx];
      const row = document.querySelector('.picker-row');
      if (row) {
        const selectWrap = row.querySelector('.picker-select-wrap');
        const trigger = row.querySelector('.picker-select');
        const qtyDisplay = row.querySelector('.qty-display');
        const thumbImg = row.querySelector('.picker-thumb img');
        if (trigger) {
          trigger.innerHTML = '<span class="picker-select-text">' + variant.name + '</span>';
          trigger.dataset.value = idx;
        }
        if (qtyDisplay) qtyDisplay.textContent = '1';
        if (thumbImg) { thumbImg.src = variant.img; thumbImg.alt = variant.name; thumbImg.classList.add('loaded','variant-selected'); }
        if (selectWrap) selectWrap.dispatchEvent(new Event('change'));
      }
    }
    if (params.get('order') === '1') {
      requestAnimationFrame(() => openModal());
    }
  }
  fetch('data/captions.json')
    .then(res => res.json())
    .then(captions => {
      const idParam = params.get('id');
      if (!idParam) {
        applyCaption({
          id: '20260318-017',
          headline: 'Going to the beach without polarized lenses?',
          vibe: 'Beach Day',
          product_ref: 'Bandits Green, Bandits Blue',
          visual_anchor: 'PRODUCT',
          card_image: ''
        });
        setPageBg('assets/ads/dubery_20260318-017.jpg');
        extractAndApplyAccent('assets/ads/dubery_20260318-017.jpg');
        return;
      }
      const caption = captions.find(c => String(c.id) === String(idParam));
      if (caption) applyCaption(caption);
      else {
        setPageBg('assets/ads/dubery_20260318-017.jpg');
        extractAndApplyAccent('assets/ads/dubery_20260318-017.jpg');
      }
    })
    .catch(() => {
      setPageBg('assets/ads/dubery_20260318-017.jpg');
      extractAndApplyAccent('assets/ads/dubery_20260318-017.jpg');
    });
}

init();

/* ── Dark Mode Toggle ────────────────────────────────────── */
(function() {
  const toggle = document.getElementById('dark-mode-toggle');
  if (!toggle) return;
  document.body.classList.add('dark-mode');
  toggle.textContent = '\u2600';
  toggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    toggle.textContent = document.body.classList.contains('dark-mode') ? '\u2600' : '\u263E';
  });
})();

/* ── Feedback Cards — click to preview + auto-scroll ─────── */
(function() {
  const scrollInner = document.querySelector('.proof-scroll-inner');
  if (!scrollInner) return;

  // Click to preview
  scrollInner.querySelectorAll('.feedback-card').forEach((card, i, all) => {
    const img = card.querySelector('.proof-img');
    const info = card.querySelector('.feedback-info');
    const name = info ? info.querySelector('.feedback-name') : null;
    const text = info ? info.querySelector('.feedback-text') : null;
    img.style.cursor = 'zoom-in';
    img.addEventListener('click', () => {
      const items = Array.from(all).map(c => ({
        src: c.querySelector('.proof-img').src,
        alt: c.querySelector('.feedback-name') ? c.querySelector('.feedback-name').textContent : 'Customer Feedback',
        desc: c.querySelector('.feedback-text') ? c.querySelector('.feedback-text').textContent : ''
      }));
      openImgPreview(img.src, name ? name.textContent : 'Customer Feedback', text ? text.textContent : '', items, i);
    });
  });

  // Auto-scroll loop -- duplicate cards for seamless looping
  const scrollEl = scrollInner.parentElement;
  if (!scrollEl) return;
  const origCards = Array.from(scrollInner.children);
  origCards.forEach(card => {
    const clone = card.cloneNode(true);
    clone.querySelector('.proof-img').addEventListener('click', () => {
      const idx = origCards.indexOf(card);
      const items = origCards.map(c => ({
        src: c.querySelector('.proof-img').src,
        alt: c.querySelector('.feedback-name') ? c.querySelector('.feedback-name').textContent : 'Customer Feedback',
        desc: c.querySelector('.feedback-text') ? c.querySelector('.feedback-text').textContent : ''
      }));
      openImgPreview(card.querySelector('.proof-img').src, items[idx].alt, items[idx].desc, items, idx);
    });
    scrollInner.appendChild(clone);
  });
  const halfWidth = scrollInner.scrollWidth / 2;
  let paused = false;
  let acc = 0;

  function autoScroll() {
    if (!paused && scrollEl.scrollWidth > scrollEl.clientWidth) {
      acc += 0.6;
      if (acc >= 1) {
        scrollEl.scrollLeft += 1;
        acc -= 1;
        if (scrollEl.scrollLeft >= halfWidth) {
          scrollEl.scrollLeft -= halfWidth;
        }
      }
      if (scrollEl.scrollLeft >= scrollEl.scrollWidth - scrollEl.clientWidth - 1) {
        scrollEl.scrollLeft = 0;
      }
    }
    requestAnimationFrame(autoScroll);
  }

  scrollEl.addEventListener('mouseenter', () => { paused = true; });
  scrollEl.addEventListener('mouseleave', () => { paused = false; dragging = false; });
  scrollEl.addEventListener('touchstart', () => { paused = true; }, { passive: true });
  scrollEl.addEventListener('touchend', () => { setTimeout(() => { paused = false; }, 2000); });

  // Mouse drag to scroll
  let dragging = false;
  let dragStartX = 0;
  let dragScrollLeft = 0;

  scrollEl.addEventListener('mousedown', (e) => {
    dragging = true;
    dragStartX = e.pageX;
    dragScrollLeft = scrollEl.scrollLeft;
    scrollEl.style.cursor = 'grabbing';
    e.preventDefault();
  });

  scrollEl.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    const dx = e.pageX - dragStartX;
    scrollEl.scrollLeft = dragScrollLeft - dx;
  });

  scrollEl.addEventListener('mouseup', () => {
    dragging = false;
    scrollEl.style.cursor = 'grab';
  });

  scrollEl.style.cursor = 'grab';

  autoScroll();
})();

/* ── Benefits Carousel ───────────────────────────────────── */
(function() {
  const track = document.getElementById('benefits-track');
  const dotsContainer = document.getElementById('benefits-dots');
  if (!track || !dotsContainer) return;
  const cards = track.querySelectorAll('.benefit-card');
  const count = cards.length;
  let current = 0;
  let startX = 0;

  for (let i = 0; i < count; i++) {
    const dot = document.createElement('button');
    dot.className = 'benefits-dot' + (i === 0 ? ' active' : '');
    dot.dataset.index = i;
    dot.addEventListener('click', () => goTo(i));
    dotsContainer.appendChild(dot);
  }
  const dots = dotsContainer.querySelectorAll('.benefits-dot');

  function goTo(idx) {
    current = (idx + count) % count;
    track.style.transform = 'translateX(-' + (current * 100) + '%)';
    dots.forEach((d, i) => d.classList.toggle('active', i === current));
  }

  track.addEventListener('touchstart', e => { startX = e.touches[0].clientX; }, { passive: true });
  track.addEventListener('touchend', e => {
    const diff = startX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 40) goTo(current + (diff > 0 ? 1 : -1));
  });
})();
