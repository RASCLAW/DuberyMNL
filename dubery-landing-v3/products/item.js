/* products/item.js — hydrate PDP from data.json using ?slug= */
'use strict';

function starsFromRating(r) {
  const full = Math.round(r);
  return '★★★★★'.slice(0, full) + '☆☆☆☆☆'.slice(0, 5 - full);
}

function addToCart(slug) {
  let cart = {};
  try { cart = JSON.parse(localStorage.getItem('dubery-cart') || '{}'); } catch (_) {}
  cart[slug] = (cart[slug] || 0) + 1;
  localStorage.setItem('dubery-cart', JSON.stringify(cart));
  if (typeof fbq !== 'undefined') fbq('track', 'AddToCart', { content_ids: [slug], content_type: 'product' });
  if (typeof updateCartBadge === 'function') updateCartBadge(true);
  return Object.values(cart).reduce((s, q) => s + q, 0);
}

(async function () {
  const root = document.querySelector('[data-pdp-root]');
  const notfound = document.querySelector('[data-pdp-notfound]');
  const slug = new URLSearchParams(location.search).get('slug');

  const res = await fetch('data.json');
  const items = await res.json();
  const p = items.find(x => x.slug === slug);

  if (!p) {
    root.hidden = true;
    notfound.hidden = false;
    document.title = 'Not found — DuberyMNL';
    return;
  }

  root.hidden = false;

  // Text fields
  const set = (sel, val) => document.querySelectorAll(`[data-field="${sel}"]`).forEach(el => { el.textContent = val; });
  document.title = `${p.name} ${p.colorway} — DuberyMNL`;
  document.querySelector('[data-field="meta-desc"]').setAttribute('content', p.copy);
  set('breadcrumb-series', p.seriesLabel);
  document.querySelector('[data-field="breadcrumb-series"]').href = `./?series=${p.series}`;
  set('breadcrumb-name', p.colorway);
  set('series-eyebrow', p.seriesLabel);
  set('name', `${p.name} ${p.colorLabel || p.colorway.split(' / ')[0]}`);
  set('colorway', p.colorway);
  set('stars', starsFromRating(p.rating));
  set('rating-text', `${p.rating.toFixed(1)} (${p.count} reviews)`);
  set('price', `₱${p.price}`);
  set('frame', p.frame);
  set('lens', p.lens);
  set('copy', p.copy);
  if (typeof fbq !== 'undefined') fbq('track', 'ViewContent', { content_name: `${p.name} ${p.colorway}`, content_ids: [p.slug], value: p.price, currency: 'PHP', content_type: 'product' });

  // Gallery
  const mainImg = document.querySelector('[data-field="gallery-main"]');
  const thumbsWrap = document.querySelector('[data-field="gallery-thumbs"]');
  const btnPrev = document.querySelector('[data-gallery-prev]');
  const btnNext = document.querySelector('[data-gallery-next]');
  let galleryIdx = 0;
  const VISIBLE_THUMBS = 8; // 2 rows on the 4-col grid; the rest collapse behind "+N more"

  function expandThumbs() {
    if (!thumbsWrap.classList.contains('is-collapsed')) return;
    thumbsWrap.classList.remove('is-collapsed');
    const more = thumbsWrap.querySelector('.pdp-thumb-more');
    if (more) more.remove();
  }

  function setGalleryIdx(idx) {
    galleryIdx = (idx + p.gallery.length) % p.gallery.length;
    mainImg.src = p.gallery[galleryIdx];
    if (galleryIdx >= VISIBLE_THUMBS) expandThumbs(); // reveal hidden thumbs when previewing into them
    thumbsWrap.querySelectorAll('.pdp-thumb').forEach((t, i) =>
      t.classList.toggle('is-active', i === galleryIdx)
    );
  }

  mainImg.src = p.gallery[0];
  mainImg.alt = `${p.name} ${p.colorway}`;
  const extraThumbs = p.gallery.length - VISIBLE_THUMBS;
  thumbsWrap.innerHTML = p.gallery.map((src, i) => {
    const hidden = i >= VISIBLE_THUMBS ? ' is-hidden' : '';
    const more = (extraThumbs > 0 && i === VISIBLE_THUMBS - 1)
      ? `<span class="pdp-thumb-more">+${extraThumbs}</span>` : '';
    return `
    <button type="button" class="pdp-thumb${i === 0 ? ' is-active' : ''}${hidden}" data-gallery-index="${i}">
      <img src="${src}" alt="" loading="lazy" decoding="async">${more}
    </button>`;
  }).join('');
  if (extraThumbs > 0) thumbsWrap.classList.add('is-collapsed');
  thumbsWrap.querySelectorAll('.pdp-thumb').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = +btn.dataset.galleryIndex;
      // Tapping the "+N" tile reveals the rest instead of just selecting it
      if (thumbsWrap.classList.contains('is-collapsed') && idx === VISIBLE_THUMBS - 1) expandThumbs();
      setGalleryIdx(idx);
    });
  });

  if (btnPrev) btnPrev.addEventListener('click', () => setGalleryIdx(galleryIdx - 1));
  if (btnNext) btnNext.addEventListener('click', () => setGalleryIdx(galleryIdx + 1));

  // Touch swipe on main image (flag a swipe so it doesn't also fire the tap-to-zoom)
  let touchStartX = 0, swiped = false;
  mainImg.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; swiped = false; }, { passive: true });
  mainImg.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(dx) > 40) { swiped = true; setGalleryIdx(galleryIdx + (dx < 0 ? 1 : -1)); }
  });

  // Tap the main image to open a fullscreen zoom (native pinch-zoom works while open)
  const lightbox = document.createElement('div');
  lightbox.className = 'pdp-lightbox';
  lightbox.hidden = true;
  lightbox.innerHTML = '<button type="button" class="pdp-lightbox-close" aria-label="Close">&times;</button><img alt="">';
  document.body.appendChild(lightbox);
  const lightboxImg = lightbox.querySelector('img');
  function openLightbox() {
    lightboxImg.src = p.gallery[galleryIdx];
    lightboxImg.alt = `${p.name} ${p.colorway}`;
    lightbox.hidden = false;
    document.body.style.overflow = 'hidden';
  }
  function closeLightbox() {
    lightbox.hidden = true;
    document.body.style.overflow = '';
  }
  mainImg.addEventListener('click', () => { if (!swiped) openLightbox(); });
  lightbox.addEventListener('click', closeLightbox);

  // Testimonial purchased chip — reflect this product in first card
  const tPurchased = document.querySelector('[data-field="t-purchased"]');
  if (tPurchased) tPurchased.textContent = `${p.name} ${p.colorLabel || p.colorway.split(' / ')[0]}`;

  // Feature image(s) — injected below testimonials if product has one or two
  const hasSingle = p.feature_image;
  const hasDual = p.feature_images && p.feature_images.length === 2;
  if (hasSingle || hasDual) {
    const testimonials = document.querySelector('.section-testimonials');
    if (testimonials) {
      const sec = document.createElement('section');
      sec.className = 'section section-soft section-feature-image';
      const inner = hasDual
        ? `<div class="feature-image-dual">
            <div class="feature-image-wrap"><img src="${p.feature_images[0]}" alt="${p.name} ${p.colorway}" loading="lazy" decoding="async"></div>
            <div class="feature-image-wrap"><img src="${p.feature_images[1]}" alt="${p.name} ${p.colorway}" loading="lazy" decoding="async"></div>
           </div>`
        : `<div class="feature-image-wrap"><img src="${p.feature_image}" alt="${p.name} ${p.colorway}" loading="lazy" decoding="async"></div>`;
      sec.innerHTML = `<div class="container"><p class="eyebrow">The look.</p>${inner}</div>`;
      testimonials.insertAdjacentElement('beforebegin', sec);
    }
  }

  // Add to Cart buttons (main CTA + mobile sticky bar)
  // Render the Most Popular card to match cart total: nudge to 2 at <2, "unlocked" at 2+
  function renderUpsell(total) {
    const card = document.querySelector('[data-pdp-upsell]');
    const ctaRow = document.querySelector('.pdp-cta-row');
    if (!card) return;
    if (total >= 2) {
      card.classList.add('is-unlocked');
      card.innerHTML =
        '<span class="b2-pop-badge b2-badge-green">Unlocked</span>'
        + '<p class="b2-pop-title">Free delivery unlocked.</p>'
        + '<p class="b2-pop-sub">2 pairs for <strong>₱998</strong> — just ₱499 each, shipping\'s on us.</p>'
        + '<a class="btn btn-primary b2-pop-cta" href="../order/">Checkout →</a>';
      if (ctaRow) ctaRow.style.display = 'none';   // card's Checkout is the action — drop the duplicate row
    } else {
      card.classList.remove('is-unlocked');
      if (ctaRow) ctaRow.style.display = '';
      card.innerHTML =
        '<span class="b2-pop-badge">Almost there</span>'
        + '<p class="b2-pop-title">You\'re 1 pair from free delivery.</p>'
        + '<p class="b2-pop-sub">Make it 2 and shipping\'s on us — <strong>₱998 for both</strong>, just ₱499 each.</p>'
        + '<div class="b2-chips">'
        + '<a class="b2-chip" href="../order/"><strong>₱598</strong>1 pair → +₱99 ship</a>'
        + '<a class="b2-chip is-deal" href="../products/"><strong>₱998</strong>2 pairs → free ship</a>'
        + '</div>';
    }
  }

  document.querySelectorAll('[data-add-to-cart]').forEach((addBtn) => {
    addBtn.addEventListener('click', () => {
      const total = addToCart(p.slug);
      const thumb = (p.gallery && p.gallery[0]) || p.thumb || p.hero;
      const label = `${p.name} ${p.colorLabel || ''}`.trim();
      if (total === 2 && typeof showBundleToast === 'function') showBundleToast();
      else if (typeof showCartToast === 'function') showCartToast(label, thumb);
      const upsell = document.querySelector('[data-pdp-upsell]');
      const copy = document.querySelector('.pdp-copy');
      renderUpsell(total);                         // update card content for the new total
      if (upsell && upsell.hidden) {
        if (copy) copy.style.display = 'none';   // replace the description with the Most Popular card
        upsell.hidden = false;
      }
      const ctaRow = document.querySelector('.pdp-cta-row');
      if (ctaRow) ctaRow.classList.add('is-post-add');  // hide Add to Cart, widen Checkout full width
    });
  });

  // SKU strip — all other products
  const others = items.filter(x => x.slug !== p.slug);

  // Inline strip (inside right column, above description) — 4 random picks
  const inlineFour = others.sort(() => Math.random() - 0.5).slice(0, 4);
  const skuInline = document.querySelector('[data-sku-inline]');
  if (skuInline) {
    skuInline.innerHTML = inlineFour.map(x => `
      <a href="item.html?slug=${encodeURIComponent(x.slug)}" class="pdp-sku-item">
        <img src="${(x.cardImages && x.cardImages[0]) || x.thumb || x.hero}" alt="${x.name} ${x.colorway}" loading="lazy" decoding="async">
        <span>${x.seriesLabel} ${x.colorLabel}</span>
      </a>
    `).join('');
  }

})();
