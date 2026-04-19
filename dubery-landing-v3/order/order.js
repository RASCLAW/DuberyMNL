/* order/order.js — multi-variant picker + totals + submit */
'use strict';

const APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxFD6z-PR8tcQhHpH-UulU-3Nk8OpqWgWeyD-J0unJser7Cptd4tP-3D6iM8W0eOoWCtg/exec';
const DELIVERY_FEE = 99;

(async function () {
  const grid = document.querySelector('[data-order-grid]');
  const itemsWrap = document.querySelector('[data-order-items]');
  const emptyMsg = document.querySelector('[data-order-empty]');
  const totalsWrap = document.querySelector('[data-order-totals]');
  const bundleNote = document.querySelector('[data-bundle-note]');
  const discountRow = document.querySelector('[data-discount-row]');
  const subtotalEl = document.querySelector('[data-subtotal]');
  const discountEl = document.querySelector('[data-discount]');
  const deliveryEl = document.querySelector('[data-delivery]');
  const grandEl = document.querySelector('[data-grand]');
  const submitBtn = document.querySelector('[data-submit]');
  const form = document.querySelector('[data-order-form]');

  const products = await fetch('../products/data.json').then(r => r.json());
  const bySlug = Object.fromEntries(products.map(p => [p.slug, p]));
  const qty = {}; // slug -> count

  // --- Render picker tiles ---
  function tile(p) {
    return `
      <div class="order-card" data-order-card data-series="${p.series}" data-slug="${p.slug}">
        <div class="order-card-media">
          <img src="${p.hero}" alt="${p.name} ${p.colorway}" loading="lazy">
        </div>
        <div class="order-card-meta">
          <div class="order-card-series">${p.seriesLabel}</div>
          <div class="order-card-name">${p.name} <span>${p.colorway}</span></div>
          <div class="order-card-price">₱${p.price}</div>
        </div>
        <div class="order-qty-controls" data-qty-for="${p.slug}">
          <button type="button" class="order-qty-btn" data-qty-op="dec" aria-label="Remove one">−</button>
          <span class="order-qty-num" data-qty-num>0</span>
          <button type="button" class="order-qty-btn order-qty-add" data-qty-op="inc" aria-label="Add one">+</button>
        </div>
      </div>
    `;
  }
  grid.innerHTML = products.map(tile).join('');

  // --- Filter pills ---
  document.querySelectorAll('.bs-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.bs-filter').forEach(b => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      const f = btn.dataset.filter;
      grid.querySelectorAll('[data-order-card]').forEach(card => {
        card.hidden = !(f === 'all' || card.dataset.series === f);
      });
    });
  });

  // --- Qty controls ---
  grid.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-qty-op]');
    if (!btn) return;
    const wrap = btn.closest('[data-qty-for]');
    const slug = wrap.dataset.qtyFor;
    const cur = qty[slug] || 0;
    const next = btn.dataset.qtyOp === 'inc' ? cur + 1 : Math.max(0, cur - 1);
    if (next === 0) delete qty[slug]; else qty[slug] = next;
    wrap.querySelector('[data-qty-num]').textContent = next;
    wrap.closest('.order-card').classList.toggle('is-picked', next > 0);
    render();
  });

  // --- Totals + summary render ---
  function totalQty() {
    return Object.values(qty).reduce((a, b) => a + b, 0);
  }
  function subtotal() {
    return Object.entries(qty).reduce((sum, [slug, n]) => sum + bySlug[slug].price * n, 0);
  }
  function render() {
    const tq = totalQty();
    const sub = subtotal();
    const bundle = tq >= 2;
    const discount = bundle ? 99 : 0;
    const delivery = bundle ? 0 : (tq > 0 ? DELIVERY_FEE : 0);
    const grand = sub - discount + delivery;

    if (tq === 0) {
      emptyMsg.hidden = false;
      totalsWrap.hidden = true;
      bundleNote.hidden = true;
      itemsWrap.querySelectorAll('.order-line').forEach(n => n.remove());
      submitBtn.disabled = true;
      return;
    }
    emptyMsg.hidden = true;
    totalsWrap.hidden = false;
    bundleNote.hidden = !bundle;

    // Line items
    itemsWrap.querySelectorAll('.order-line').forEach(n => n.remove());
    Object.entries(qty).forEach(([slug, n]) => {
      const p = bySlug[slug];
      const line = document.createElement('div');
      line.className = 'order-line';
      line.innerHTML = `
        <img class="order-line-thumb" src="${p.thumb}" alt="">
        <div class="order-line-meta">
          <div class="order-line-name">${p.name} <span>${p.colorway}</span></div>
          <div class="order-line-sub">₱${p.price} × ${n}</div>
        </div>
        <div class="order-line-total">₱${p.price * n}</div>
        <button type="button" class="order-line-remove" data-remove="${slug}" aria-label="Remove">×</button>
      `;
      itemsWrap.appendChild(line);
    });

    subtotalEl.textContent = `₱${sub}`;
    discountRow.hidden = !bundle;
    discountEl.textContent = `−₱${discount}`;
    deliveryEl.textContent = delivery === 0 ? 'Free' : `₱${delivery}`;
    grandEl.textContent = `₱${grand}`;
    submitBtn.disabled = false;
  }

  // Remove line item
  itemsWrap.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-remove]');
    if (!btn) return;
    const slug = btn.dataset.remove;
    delete qty[slug];
    const card = grid.querySelector(`[data-slug="${slug}"]`);
    if (card) {
      card.classList.remove('is-picked');
      card.querySelector('[data-qty-num]').textContent = '0';
    }
    render();
  });

  // --- Pre-fill from ?model=&qty= ---
  const params = new URLSearchParams(location.search);
  const preModel = params.get('model');
  const preQty = Math.max(1, parseInt(params.get('qty') || '1', 10));
  if (preModel && bySlug[preModel]) {
    qty[preModel] = preQty;
    const card = grid.querySelector(`[data-slug="${preModel}"]`);
    if (card) {
      card.classList.add('is-picked');
      card.querySelector('[data-qty-num]').textContent = preQty;
    }
  }
  render();

  // --- Submit ---
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (totalQty() === 0) return;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Placing order…';
    const data = new FormData(form);
    const tq = totalQty();
    const bundle = tq >= 2;
    const discount = bundle ? 99 : 0;
    const delivery = bundle ? 0 : DELIVERY_FEE;
    const grand = subtotal() - discount + delivery;

    const items = Object.entries(qty).map(([slug, n]) => ({
      name: bySlug[slug].order_name,
      qty: n,
    }));

    const payload = {
      name: data.get('name'),
      phone: data.get('phone'),
      address: data.get('address'),
      notes: data.get('notes') || '',
      items,
      caption_id: 'order_form',
      grand_total: grand,
      delivery_fee: delivery,
      express: false,
    };
    try {
      const formData = new FormData();
      formData.append('payload', JSON.stringify(payload));
      await fetch(APPS_SCRIPT_URL, {
        method: 'POST',
        mode: 'no-cors',
        body: formData,
      });
      document.querySelector('.order-summary-card').innerHTML = `
        <div class="pdp-success">
          <p class="eyebrow">Order placed.</p>
          <h3>Salamat, ${payload.name.split(' ')[0]}!</h3>
          <p>${tq} pair${tq > 1 ? 's' : ''} locked in. We'll confirm by SMS or Messenger shortly. Cash on delivery.</p>
          <a class="btn btn-primary" href="https://m.me/duberymnl?ref=order_confirm" target="_blank" rel="noopener">Message us</a>
        </div>
      `;
    } catch (err) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Place order';
      alert('Hmm, something went wrong. Please try Messenger instead.');
    }
  });
})();
