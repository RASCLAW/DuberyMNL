/* products/item.js — hydrate PDP from data.json using ?slug= */
'use strict';

const APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxFD6z-PR8tcQhHpH-UulU-3Nk8OpqWgWeyD-J0unJser7Cptd4tP-3D6iM8W0eOoWCtg/exec';

function starsFromRating(r) {
  const full = Math.round(r);
  return '★★★★★'.slice(0, full) + '☆☆☆☆☆'.slice(0, 5 - full);
}

function renderRelatedCard(p) {
  const href = `item.html?slug=${encodeURIComponent(p.slug)}`;
  return `
    <a href="${href}" class="bs-card related-card" data-series="${p.series}">
      <div class="bs-media">
        <img class="bs-img primary" src="${p.hero}" alt="${p.name} ${p.colorway}" loading="lazy">
        <img class="bs-img hover" src="${p.hover}" alt="" loading="lazy">
      </div>
      <div class="bs-meta">
        <div class="bs-rating">
          <span class="bs-stars">${starsFromRating(p.rating)}</span>
          <span class="bs-count">(${p.count})</span>
        </div>
        <h3 class="bs-title">${p.name.toUpperCase()} <span class="bs-colorway">| ${p.colorway}</span></h3>
        <div class="bs-price">₱${p.price}</div>
      </div>
    </a>
  `;
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
  set('name', `${p.name} ${p.colorway.split(' / ')[0]}`);
  set('colorway', p.colorway);
  set('stars', starsFromRating(p.rating));
  set('rating-text', `${p.rating.toFixed(1)} (${p.count} reviews)`);
  set('price', `₱${p.price}`);
  set('frame', p.frame);
  set('lens', p.lens);
  set('copy', p.copy);
  set('subtotal', `₱${p.price}`);
  set('total', `₱${p.price + 99}`);

  // Gallery
  const mainImg = document.querySelector('[data-field="gallery-main"]');
  mainImg.src = p.gallery[0];
  mainImg.alt = `${p.name} ${p.colorway}`;
  const thumbsWrap = document.querySelector('[data-field="gallery-thumbs"]');
  thumbsWrap.innerHTML = p.gallery.map((src, i) => `
    <button type="button" class="pdp-thumb${i === 0 ? ' is-active' : ''}" data-gallery-index="${i}">
      <img src="${src}" alt="" loading="lazy">
    </button>
  `).join('');
  thumbsWrap.querySelectorAll('.pdp-thumb').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = +btn.dataset.galleryIndex;
      mainImg.src = p.gallery[idx];
      thumbsWrap.querySelectorAll('.pdp-thumb').forEach(t => t.classList.remove('is-active'));
      btn.classList.add('is-active');
    });
  });

  // Messenger deep-link with ref
  document.querySelector('[data-field="messenger"]').href = `https://m.me/duberymnl?ref=pdp_${p.slug}`;

  // Qty pills
  const qtyPills = document.querySelectorAll('.qty-pill');
  const totalEl = document.querySelector('[data-field="total"]');
  let selectedQty = 1;
  qtyPills.forEach(pill => {
    pill.addEventListener('click', () => {
      const q = +pill.dataset.qty;
      if (q === 2) {
        // 2 pairs means mix colorways — route to /order/ with this variant pre-picked
        location.href = `../order/?model=${encodeURIComponent(p.slug)}&qty=1`;
        return;
      }
      qtyPills.forEach(x => x.classList.remove('is-active'));
      pill.classList.add('is-active');
      selectedQty = q;
      totalEl.textContent = `₱${p.price + 99}`;
    });
  });

  // Testimonial purchased chip — reflect this product in first card
  const tPurchased = document.querySelector('[data-field="t-purchased"]');
  if (tPurchased) tPurchased.textContent = `${p.name} ${p.colorway.split(' / ')[0]}`;

  // Related — 4 random others
  const others = items.filter(x => x.slug !== p.slug);
  const sameSeries = others.filter(x => x.series === p.series);
  const diffSeries = others.filter(x => x.series !== p.series);
  const related = [...sameSeries, ...diffSeries].slice(0, 4);
  document.querySelector('[data-related-grid]').innerHTML = related.map(renderRelatedCard).join('');

  // Form submit
  const form = document.querySelector('[data-pdp-form]');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('.pdp-submit');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Placing order…';
    const data = new FormData(form);
    // PDP is single-pair only (qty=2 routes to /order/). ₱99 delivery.
    const delivery = 99;
    const grand = p.price + delivery;
    const payload = {
      name: data.get('name'),
      phone: data.get('phone'),
      address: data.get('address'),
      notes: data.get('notes') || '',
      items: [{ name: p.order_name, qty: 1 }],
      caption_id: `pdp_${p.slug}`,
      grand_total: grand,
      delivery_fee: delivery,
      express: false,
    };
    try {
      const fd = new FormData();
      fd.append('payload', JSON.stringify(payload));
      await fetch(APPS_SCRIPT_URL, {
        method: 'POST',
        mode: 'no-cors',
        body: fd,
      });
      form.innerHTML = `
        <div class="pdp-success">
          <p class="eyebrow">Order placed.</p>
          <h3>Salamat, ${payload.name.split(' ')[0]}!</h3>
          <p>We'll confirm your order by SMS or Messenger shortly. No payment needed until delivery.</p>
          <a class="btn btn-primary" href="https://m.me/duberymnl?ref=pdp_confirm_${p.slug}" target="_blank" rel="noopener">Message us</a>
        </div>
      `;
    } catch (err) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Place order';
      alert('Hmm, something went wrong. Please try Messenger instead.');
    }
  });
})();
