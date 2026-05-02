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
  if (typeof updateCartBadge === 'function') updateCartBadge();
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
  const set = (sel, val) => document.querySelector(`[data-field="${sel}"]`).textContent = val;
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

  // Gallery
  const mainImg = document.querySelector('[data-field="gallery-main"]');
  const thumbsWrap = document.querySelector('[data-field="gallery-thumbs"]');
  const btnPrev = document.querySelector('[data-gallery-prev]');
  const btnNext = document.querySelector('[data-gallery-next]');
  let galleryIdx = 0;

  function setGalleryIdx(idx) {
    galleryIdx = (idx + p.gallery.length) % p.gallery.length;
    mainImg.src = p.gallery[galleryIdx];
    thumbsWrap.querySelectorAll('.pdp-thumb').forEach((t, i) =>
      t.classList.toggle('is-active', i === galleryIdx)
    );
  }

  mainImg.src = p.gallery[0];
  mainImg.alt = `${p.name} ${p.colorway}`;
  thumbsWrap.innerHTML = p.gallery.map((src, i) => `
    <button type="button" class="pdp-thumb${i === 0 ? ' is-active' : ''}" data-gallery-index="${i}">
      <img src="${src}" alt="" loading="lazy">
    </button>
  `).join('');
  thumbsWrap.querySelectorAll('.pdp-thumb').forEach(btn => {
    btn.addEventListener('click', () => setGalleryIdx(+btn.dataset.galleryIndex));
  });

  if (btnPrev) btnPrev.addEventListener('click', () => setGalleryIdx(galleryIdx - 1));
  if (btnNext) btnNext.addEventListener('click', () => setGalleryIdx(galleryIdx + 1));

  // Touch swipe on main image
  let touchStartX = 0;
  mainImg.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; }, { passive: true });
  mainImg.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(dx) > 40) setGalleryIdx(galleryIdx + (dx < 0 ? 1 : -1));
  });

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
            <div class="feature-image-wrap"><img src="${p.feature_images[0]}" alt="${p.name} ${p.colorway}" loading="lazy"></div>
            <div class="feature-image-wrap"><img src="${p.feature_images[1]}" alt="${p.name} ${p.colorway}" loading="lazy"></div>
           </div>`
        : `<div class="feature-image-wrap"><img src="${p.feature_image}" alt="${p.name} ${p.colorway}" loading="lazy"></div>`;
      sec.innerHTML = `<div class="container"><p class="eyebrow">The look.</p>${inner}</div>`;
      testimonials.insertAdjacentElement('beforebegin', sec);
    }
  }

  // Add to Cart button
  const addBtn = document.querySelector('[data-add-to-cart]');
  if (addBtn) {
    let added = false;
    addBtn.addEventListener('click', () => {
      if (added) { window.location.href = '../products/'; return; }
      added = true;
      addToCart(p.slug);
      addBtn.textContent = 'Added ✓';
      addBtn.classList.add('is-added');
      addBtn.disabled = true;
      setTimeout(() => {
        addBtn.textContent = 'Shop All';
        addBtn.classList.remove('is-added');
        addBtn.disabled = false;
      }, 1500);
    });
  }

  // SKU strip — all other products
  const others = items.filter(x => x.slug !== p.slug);

  // Inline strip (inside right column, above description) — 4 random picks
  const inlineFour = others.sort(() => Math.random() - 0.5).slice(0, 4);
  const skuInline = document.querySelector('[data-sku-inline]');
  if (skuInline) {
    skuInline.innerHTML = inlineFour.map(x => `
      <a href="item.html?slug=${encodeURIComponent(x.slug)}" class="pdp-sku-item">
        <img src="${x.thumb || x.hero}" alt="${x.name} ${x.colorway}" loading="lazy">
        <span>${x.seriesLabel} ${x.colorLabel}</span>
      </a>
    `).join('');
  }

})();
