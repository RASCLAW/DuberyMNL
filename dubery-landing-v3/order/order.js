/* order/order.js — product grid (series accordion) + totals + submit */
'use strict';

const APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxFD6z-PR8tcQhHpH-UulU-3Nk8OpqWgWeyD-J0unJser7Cptd4tP-3D6iM8W0eOoWCtg/exec';
const DELIVERY_FEE = 99;
const COD_FEE = 50;

(async function () {
  const productGridEl = document.querySelector('[data-product-grid]');
  const itemsWrap    = document.querySelector('[data-order-items]');
  const emptyMsg     = document.querySelector('[data-order-empty]');
  const totalsWrap   = document.querySelector('[data-order-totals]');
  const bundleNote   = document.querySelector('[data-bundle-note]');
  const upsellBar    = document.querySelector('[data-upsell-bar]');
  const discountRow  = document.querySelector('[data-discount-row]');
  const codRow       = document.querySelector('[data-cod-row]');
  const subtotalEl   = document.querySelector('[data-subtotal]');
  const deliveryEl   = document.querySelector('[data-delivery]');
  const codEl        = document.querySelector('[data-cod]');
  const grandEl      = document.querySelector('[data-grand]');
  const submitBtn    = document.querySelector('[data-submit]');
  const form         = document.querySelector('[data-order-form]');

  const products = await fetch('../products/data.json').then(r => r.json());
  const bySlug = Object.fromEntries(products.map(p => [p.slug, p]));

  // qtys: { slug: number }
  const qtys = {};
  products.forEach(p => { qtys[p.slug] = 0; });

  // Pre-populate from localStorage cart
  try {
    const saved = JSON.parse(localStorage.getItem('dubery-cart') || '{}');
    Object.entries(saved).forEach(([s, q]) => { if (s in qtys) qtys[s] = q; });
  } catch (_) {}

  function saveCart() {
    const out = {};
    products.forEach(p => { if (qtys[p.slug] > 0) out[p.slug] = qtys[p.slug]; });
    if (Object.keys(out).length === 0) {
      localStorage.removeItem('dubery-cart');
    } else {
      localStorage.setItem('dubery-cart', JSON.stringify(out));
    }
    if (typeof updateCartBadge === 'function') updateCartBadge();
  }

  // card element refs by slug
  const cardEls = {};

  function getItems() {
    return products
      .filter(p => qtys[p.slug] > 0)
      .map(p => ({ slug: p.slug, qty: qtys[p.slug], product: p }));
  }
  function totalQty() { return getItems().reduce((s, i) => s + i.qty, 0); }
  function subtotal() { return getItems().reduce((s, i) => s + i.product.price * i.qty, 0); }

  // --- Build product grid grouped by series ---
  const seriesOrder  = ['bandits', 'outback', 'rasta'];
  const seriesLabels = { bandits: 'Bandits', outback: 'Outback', rasta: 'Rasta' };

  seriesOrder.forEach((series, idx) => {
    const group = document.createElement('div');
    group.className = 'order-series-group';

    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'order-series-toggle';
    toggle.dataset.series = series;
    toggle.innerHTML = `<span class="order-series-label">${seriesLabels[series]}</span><span class="order-series-hint">click to expand</span><span class="order-series-arrow">►</span>`;

    const grid = document.createElement('div');
    grid.className = 'order-series-grid';
    grid.hidden = true;

    products.filter(p => p.series === series).forEach(p => {
      const card = document.createElement('div');
      card.className = 'order-product-card';
      card.dataset.slug = p.slug;

      const img = document.createElement('img');
      img.className = 'order-product-img';
      img.src = p.hero;
      img.alt = p.colorway;
      img.loading = 'lazy';

      const meta = document.createElement('div');
      meta.className = 'order-product-meta';
      meta.innerHTML = `<div class="order-product-name">${p.name} ${p.colorLabel || p.colorway.split(' / ')[0]}</div><div class="order-product-price">&#8369;${p.price}</div>`;

      const qtyDisplay = document.createElement('span');
      qtyDisplay.className = 'stepper-qty';
      qtyDisplay.textContent = '0';

      const btnMinus = document.createElement('button');
      btnMinus.type = 'button';
      btnMinus.className = 'stepper-btn';
      btnMinus.textContent = '−';
      btnMinus.setAttribute('aria-label', 'Remove one');

      const btnPlus = document.createElement('button');
      btnPlus.type = 'button';
      btnPlus.className = 'stepper-btn stepper-btn-add';
      btnPlus.textContent = '+';
      btnPlus.setAttribute('aria-label', 'Add one');

      const stepper = document.createElement('div');
      stepper.className = 'stepper';
      stepper.append(btnMinus, qtyDisplay, btnPlus);

      card.append(img, meta, stepper);
      grid.appendChild(card);
      cardEls[p.slug] = { card, qtyDisplay };

      btnPlus.addEventListener('click', () => {
        qtys[p.slug]++;
        qtyDisplay.textContent = qtys[p.slug];
        card.classList.add('is-active');
        saveCart();
        render();
      });

      btnMinus.addEventListener('click', () => {
        if (qtys[p.slug] === 0) return;
        qtys[p.slug]--;
        qtyDisplay.textContent = qtys[p.slug];
        card.classList.toggle('is-active', qtys[p.slug] > 0);
        saveCart();
        render();
      });
    });

    toggle.addEventListener('click', () => {
      const isOpen = !grid.hidden;
      grid.hidden = isOpen;
      toggle.querySelector('.order-series-arrow').textContent = isOpen ? '►' : '▼';
      toggle.classList.toggle('is-open', !isOpen);
    });

    group.append(toggle, grid);
    productGridEl.appendChild(group);
  });

  // Sync stepper UI with any pre-loaded qtys (from localStorage)
  let hasPreloaded = false;
  products.forEach(p => {
    if (qtys[p.slug] > 0 && cardEls[p.slug]) {
      cardEls[p.slug].card.classList.add('is-active');
      cardEls[p.slug].qtyDisplay.textContent = qtys[p.slug];
      hasPreloaded = true;
    }
  });

  // --- Totals + summary sidebar ---
  function render() {
    const items = getItems();
    const tq = totalQty();
    const sub = subtotal();
    const bundle = tq >= 2;
    const delivery = bundle ? 0 : (tq > 0 ? DELIVERY_FEE : 0);
    const cod = bundle ? 0 : (tq > 0 ? COD_FEE : 0);
    const grand = sub + delivery + cod;

    if (tq === 0) {
      emptyMsg.hidden = false;
      totalsWrap.hidden = true;
      bundleNote.hidden = true;
      upsellBar.hidden = true;
      itemsWrap.querySelectorAll('.order-line').forEach(n => n.remove());
      submitBtn.disabled = true;
      return;
    }
    emptyMsg.hidden = true;
    totalsWrap.hidden = false;
    bundleNote.hidden = !bundle;
    upsellBar.hidden = bundle;

    itemsWrap.querySelectorAll('.order-line').forEach(n => n.remove());
    items.forEach(({ slug, qty: n, product: p }) => {
      const line = document.createElement('div');
      line.className = 'order-line';
      line.innerHTML = `
        <img class="order-line-thumb" src="${p.thumb}" alt="">
        <div class="order-line-meta">
          <div class="order-line-name">${p.name} <span>${p.colorLabel || p.colorway.split(' / ')[0]}</span></div>
          <div class="order-line-sub">&#8369;${p.price} &times; ${n}</div>
        </div>
        <div class="order-line-total">&#8369;${p.price * n}</div>
        <button type="button" class="order-line-remove" data-remove="${slug}" aria-label="Remove">&times;</button>
      `;
      itemsWrap.appendChild(line);
    });

    subtotalEl.textContent = `₱${sub}`;
    discountRow.hidden = true;
    deliveryEl.textContent = delivery === 0 ? 'Free' : `₱${delivery}`;
    codRow.style.display = cod ? '' : 'none';
    if (codEl) codEl.textContent = `₱${COD_FEE}`;
    grandEl.textContent = `₱${grand}`;
    submitBtn.disabled = false;
  }

  // Remove via sidebar ×
  itemsWrap.addEventListener('click', e => {
    const btn = e.target.closest('[data-remove]');
    if (!btn) return;
    const slug = btn.dataset.remove;
    qtys[slug] = 0;
    if (cardEls[slug]) {
      cardEls[slug].card.classList.remove('is-active');
      cardEls[slug].qtyDisplay.textContent = '0';
    }
    saveCart();
    render();
  });

  // --- Submit ---
  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (totalQty() === 0) return;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Placing order…';
    const data = new FormData(form);
    const tq = totalQty();
    const bundle = tq >= 2;
    const delivery = bundle ? 0 : DELIVERY_FEE;
    const cod = bundle ? 0 : COD_FEE;
    const grand = subtotal() + delivery + cod;
    const items = getItems().map(({ slug, qty: n }) => ({
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
      cod_fee: cod,
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
      localStorage.removeItem('dubery-cart');
      if (typeof updateCartBadge === 'function') updateCartBadge();
      // Local backup
      try {
        const log = JSON.parse(localStorage.getItem('dubery-orders-log') || '[]');
        log.push({ ...payload, timestamp: new Date().toISOString() });
        localStorage.setItem('dubery-orders-log', JSON.stringify(log));
      } catch (_) {}
      document.querySelector('.order-summary-card').innerHTML = `
        <div class="pdp-success">
          <p class="eyebrow">Order placed.</p>
          <h3>Salamat, ${payload.name.split(' ')[0]}!</h3>
          <p>${tq} pair${tq > 1 ? 's' : ''} locked in. We'll confirm by SMS or Messenger shortly. Cash on delivery.</p>
          <a class="btn btn-primary" href="https://facebook.com/duberymnl" target="_blank" rel="noopener">Message us</a>
        </div>
      `;
    } catch (err) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Place order';
      alert('Hmm, something went wrong. Please try Messenger instead.');
    }
  });

  // --- URL param pre-select ---
  const params   = new URLSearchParams(location.search);
  const preModel = params.get('model');
  const preQty   = Math.max(1, parseInt(params.get('qty') || '1', 10));
  if (preModel && bySlug[preModel]) {
    qtys[preModel] = preQty;
    if (cardEls[preModel]) {
      cardEls[preModel].card.classList.add('is-active');
      cardEls[preModel].qtyDisplay.textContent = preQty;
    }
    const series      = bySlug[preModel].series;
    const groupToggle = productGridEl.querySelector(`[data-series="${series}"]`);
    const groupGrid   = groupToggle?.nextElementSibling;
    if (groupGrid)   groupGrid.hidden = false;
    if (groupToggle) groupToggle.querySelector('.order-series-arrow').textContent = '▼';
    if (series !== 'bandits') {
      const banditsToggle = productGridEl.querySelector('[data-series="bandits"]');
      const banditsGrid   = banditsToggle?.nextElementSibling;
      if (banditsGrid)   banditsGrid.hidden = true;
      if (banditsToggle) banditsToggle.querySelector('.order-series-arrow').textContent = '►';
    }
    render();
  } else if (hasPreloaded) {
    render();
  }
})();
