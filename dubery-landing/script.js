/* ============================================================
   DUBERY LANDING PAGE — script.js
   Dynamic caption loading · Modal · Picker · Form submit
   ============================================================ */

'use strict';

/* ── Config ───────────────────────────────────────────────── */
// Set this after Google Apps Script is deployed
const FORM_ENDPOINT = '';

/* ── Product image map ────────────────────────────────────── */
const PRODUCT_IMAGE_MAP = [
  { keys: ['outback black'],                   img: 'assets/outback-black.png',        label: 'DUBERY OUTBACK BLACK POLARIZED'        },
  { keys: ['outback blue'],                    img: 'assets/outback-blue.png',         label: 'DUBERY OUTBACK BLUE POLARIZED'         },
  { keys: ['outback red'],                     img: 'assets/outback-red.png',          label: 'DUBERY OUTBACK RED POLARIZED'          },
  { keys: ['outback green'],                   img: 'assets/outback-green.png',        label: 'DUBERY OUTBACK GREEN POLARIZED'        },
  { keys: ['outback series', 'outback'],       img: 'assets/outback-black.png',        label: 'DUBERY OUTBACK SERIES POLARIZED'       },
  { keys: ['bandits camo'],                    img: 'assets/bandits-camo.png',         label: 'DUBERY BANDITS CAMO POLARIZED'         },
  { keys: ['bandits glossy black','bandits black'], img: 'assets/bandits-glossy-black.png', label: 'DUBERY BANDITS POLARIZED'         },
  { keys: ['bandits green', 'bandits blue'],   img: 'assets/bandits-green-blue.png',   label: 'DUBERY BANDITS POLARIZED'              },
  { keys: ['bandits tortoise'],                img: 'assets/bandits-tortoise.png',     label: 'DUBERY BANDITS TORTOISE POLARIZED'     },
  { keys: ['rasta red'],                       img: 'assets/rasta-red-card.png',       label: 'DUBERY RASTA RED POLARIZED'            },
  { keys: ['rasta brown'],                     img: 'assets/rasta-brown.png',          label: 'DUBERY RASTA BROWN POLARIZED'          },
  { keys: ['rasta series', 'rasta'],           img: 'assets/rasta-red-card.png',       label: 'DUBERY RASTA SERIES POLARIZED'         },
  { keys: ['bundle', 'mixed'],                 img: 'assets/bundle.jpg',               label: 'DUBERY POLARIZED BUNDLE'               },
];

const PRODUCT_DEFAULT = { img: 'assets/outback-black.png', label: 'DUBERY POLARIZED SUNGLASSES' };

function resolveProductImage(productRef) {
  if (!productRef) return PRODUCT_DEFAULT;
  const ref = productRef.toLowerCase();
  // Multi-model (has comma) → bundle
  if (ref.includes(',')) return { img: 'assets/bundle.jpg', label: 'DUBERY POLARIZED BUNDLE' };
  for (const entry of PRODUCT_IMAGE_MAP) {
    if (entry.keys.some(k => ref.includes(k))) {
      return { img: entry.img, label: entry.label };
    }
  }
  return PRODUCT_DEFAULT;
}

/* ── Variant data ─────────────────────────────────────────── */
const VARIANTS = [
  { name: 'Outback – Black',        img: 'assets/outback-black.png' },
  { name: 'Outback – Blue',         img: 'assets/outback-blue.png' },
  { name: 'Outback – Red',          img: 'assets/outback-red.png' },
  { name: 'Outback – Green',        img: 'assets/outback-green.png' },
  { name: 'Rasta – Red',            img: 'assets/rasta-red.png' },
  { name: 'Rasta – Brown',          img: 'assets/rasta-brown.png' },
  { name: 'Bandits – Camo',         img: 'assets/bandits-camo.png' },
  { name: 'Bandits – Glossy Black', img: 'assets/bandits-glossy-black.png' },
  { name: 'Bandits – Green Blue',   img: 'assets/bandits-green-blue.png' },
  { name: 'Bandits – Tortoise',     img: 'assets/bandits-tortoise.png' },
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
  if (pairs === 1) return 699;
  if (pairs === 2) return 1200;
  if (pairs === 3) return 1800;
  if (pairs === 4) return 2300;
  return 2300 + (pairs - 4) * 500;
}
const submitBtn    = document.getElementById('submit-btn');

/* ── State ────────────────────────────────────────────────── */
let activeCaptionId = null;

/* ── Google Maps Places Autocomplete ─────────────────────── */
window.initMaps = function() {
  const addressInput = document.getElementById('field-address');
  if (!addressInput || !window.google) return;

  const autocomplete = new google.maps.places.Autocomplete(addressInput, {
    componentRestrictions: { country: 'ph' },
    fields: ['formatted_address'],
  });

  autocomplete.addListener('place_changed', () => {
    const place = autocomplete.getPlace();
    if (place && place.formatted_address) {
      addressInput.value = place.formatted_address;
      addressInput.dispatchEvent(new Event('input'));
    }
  });
}

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

      if (bestScore > 0) applyTheme(bestH, bestS);
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

  // Swap hero image + extract accent + set blurred page bg
  const imgUrl = `assets/ads/dubery_${caption.id}.jpg`;
  heroBg.style.backgroundImage = `url('${imgUrl}')`;
  setPageBg(imgUrl);
  extractAndApplyAccent(imgUrl);

  // Swap product card image + label
  const productPhoto = document.getElementById('product-photo');
  const productName  = document.getElementById('product-name');
  const resolved = caption.card_image
    ? { img: `assets/${caption.card_image}`, label: resolveProductImage(caption.product_ref).label }
    : resolveProductImage(caption.product_ref);
  if (productPhoto) productPhoto.src = resolved.img;
  if (productName)  productName.textContent = resolved.label;

  // Swap headline + sub (elements may not exist if removed from template)
  if (caption.headline && heroHeadline) heroHeadline.textContent = caption.headline;
  if (caption.vibe && heroSub) heroSub.textContent = `${caption.vibe} · Polarized Sunglasses`;
}

function loadCaption() {
  const params = new URLSearchParams(window.location.search);
  const idParam = params.get('id');
  if (!idParam) return; // No ID — keep defaults

  const captionId = parseInt(idParam, 10);
  if (isNaN(captionId)) return;

  fetch('data/captions.json')
    .then(res => res.json())
    .then(captions => {
      const caption = captions.find(c => c.id === captionId);
      if (caption) {
        applyCaption(caption);
      }
      // If not found: keep defaults
    })
    .catch(() => {
      // Fetch failed — keep defaults silently
    });
}

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
function openImgPreview(src, alt) {
  const previewImg = document.getElementById('img-preview-img');
  previewImg.src = src;
  previewImg.alt = alt || '';
  imgPreviewOverlay.classList.add('active');
  imgPreviewOverlay.setAttribute('aria-hidden', 'false');
}
imgPreviewOverlay.addEventListener('click', closeImgPreview);

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
  const select = document.createElement('select');
  select.className = 'picker-select';
  select.setAttribute('aria-label', 'Select a variant');

  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'Select a variant...';
  placeholder.disabled = true;
  placeholder.selected = true;
  select.appendChild(placeholder);

  VARIANTS.forEach((v, i) => {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = v.name;
    select.appendChild(opt);
  });

  return select;
}

function addPickerRow() {
  const row = document.createElement('div');
  row.className = 'picker-row';

  const thumb = document.createElement('div');
  thumb.className = 'picker-thumb';
  const thumbImg = document.createElement('img');
  thumbImg.alt = '';
  thumbImg.src = '';
  thumb.style.cursor = 'pointer';
  thumb.addEventListener('click', () => {
    if (!thumbImg.src || !thumbImg.classList.contains('loaded')) return;
    openImgPreview(thumbImg.src, thumbImg.alt);
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
    if (isNaN(idx)) return;
    const variant = VARIANTS[idx];
    thumbImg.src = variant.img + '?v=' + Date.now();
    thumbImg.alt = variant.name;
    thumbImg.classList.remove('loaded');
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
    const sel = row.querySelector('.picker-select');
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
    li.querySelector('.summary-line-img').addEventListener('click', () => openImgPreview(item.img, item.name));
    summaryLines.appendChild(li);
  });

  // Freebies line — 1 set per pair ordered
  const incLi = document.createElement('li');
  incLi.className = 'summary-line summary-line-inclusions';
  incLi.innerHTML = `<img class="summary-line-img" src="assets/inclusions.png" alt="Freebies" /><span class="summary-line-name">Freebies</span><span class="summary-line-qty">x${total}</span>`;
  incLi.querySelector('.summary-line-img').addEventListener('click', () => openImgPreview('assets/inclusions.png', 'Freebies'));
  summaryLines.appendChild(incLi);

  totalCount.textContent = total;
  summaryNudge.hidden = total !== 1;
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
    const sel = row.querySelector('.picker-select');
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
  const payload = { name, phone, address, items, notes, caption_id: activeCaptionId };

  // Submit to Google Apps Script endpoint (if configured)
  if (FORM_ENDPOINT) {
    submitBtn.classList.add('loading');
    submitBtn.textContent = 'Submitting...';

    try {
      await fetch(FORM_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
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
  if (params.get('id')) {
    loadCaption(); // Dynamic: reads ?id= from URL
  } else {
    // No ?id= — apply default caption (#32 = hero.jpg)
    fetch('data/captions.json')
      .then(res => res.json())
      .then(captions => {
        const def = captions.find(c => c.id === 32);
        if (def) applyCaption(def);
        else {
          setPageBg('assets/hero.png');
          extractAndApplyAccent('assets/hero.png');
        }
      })
      .catch(() => {
        setPageBg('assets/hero.png');
        extractAndApplyAccent('assets/hero.png');
      });
  }
}

init();
