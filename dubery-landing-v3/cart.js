/* cart.js — shared cart badge updater, included on every page */
'use strict';

function updateCartBadge() {
  let cart = {};
  try { cart = JSON.parse(localStorage.getItem('dubery-cart') || '{}'); } catch (_) {}
  const total = Object.values(cart).reduce((s, q) => s + q, 0);
  document.querySelectorAll('.cart-badge').forEach(el => {
    el.textContent = total;
    el.style.display = total === 0 ? 'none' : '';
  });
  const note = document.querySelector('[data-delivery-note]');
  if (note) {
    if (total >= 2) {
      note.textContent = 'Free delivery applied.';
      note.style.color = '#1e7a46';
    } else {
      note.textContent = 'Add one more pair for FREE DELIVERY PROMO.';
      note.style.color = '';
    }
  }
}

updateCartBadge();
