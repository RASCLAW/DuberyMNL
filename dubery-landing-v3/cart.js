/* cart.js — shared cart badge updater + ad attribution capture, included on every page */
'use strict';

/* Capture ad attribution from URL on every page load.
   Meta auto-substitutes {{ad.id}} in destination URLs, so we add
   ?utm_content={{ad.id}} to ad URLs in Ads Manager and read it here.
   Persisted to localStorage so it survives navigation (homepage → PDP → order).
   First-touch wins: don't overwrite an existing attribution unless a new ad click brings one in. */
(function captureAttribution() {
  try {
    const params = new URLSearchParams(location.search);
    const adId    = params.get('utm_content');
    const source  = params.get('utm_source');
    const campaign = params.get('utm_campaign');
    const fbclid  = params.get('fbclid');
    if (!adId && !source && !campaign && !fbclid) return;

    const existing = JSON.parse(localStorage.getItem('dubery-attribution') || 'null');
    // If existing has an ad_id and this visit doesn't, keep first-touch.
    if (existing && existing.ad_id && !adId) return;

    const record = {
      ad_id: adId || (existing && existing.ad_id) || '',
      utm_source: source || (existing && existing.utm_source) || '',
      utm_campaign: campaign || (existing && existing.utm_campaign) || '',
      fbclid: fbclid || (existing && existing.fbclid) || '',
      landing_page: location.pathname,
      first_seen: (existing && existing.first_seen) || new Date().toISOString(),
      last_seen: new Date().toISOString(),
    };
    localStorage.setItem('dubery-attribution', JSON.stringify(record));
  } catch (_) {}
})();

function updateCartBadge(animate) {
  let cart = {};
  try { cart = JSON.parse(localStorage.getItem('dubery-cart') || '{}'); } catch (_) {}
  const total = Object.values(cart).reduce((s, q) => s + q, 0);
  document.querySelectorAll('.cart-badge').forEach(el => {
    el.textContent = total;
    el.style.display = total === 0 ? 'none' : '';
    if (animate) { el.classList.remove('cart-bump'); void el.offsetWidth; el.classList.add('cart-bump'); }
  });
  const note = document.querySelector('[data-delivery-note]');
  if (note) {
    if (total >= 2) {
      note.textContent = 'FREE delivery applied';
      note.classList.add('is-applied');
    } else {
      note.textContent = '2 pairs = FREE delivery';
      note.classList.remove('is-applied');
    }
  }
}

/* Add-to-cart visual feedback (toast + badge bump) — shared on every page */
(function injectCartFeedbackStyles() {
  if (document.getElementById('cart-feedback-styles')) return;
  const s = document.createElement('style');
  s.id = 'cart-feedback-styles';
  s.textContent = ''
    + '.cart-badge.cart-bump{animation:cartBump .45s cubic-bezier(.2,.9,.3,1.4)}'
    + '@keyframes cartBump{0%{transform:scale(1)}35%{transform:scale(1.6)}100%{transform:scale(1)}}'
    + '.cart-toast{position:fixed;left:50%;bottom:24px;transform:translate(-50%,170%);z-index:1200;display:flex;align-items:center;gap:12px;background:#1a1a1a;color:#fff;padding:13px 17px;border-radius:14px;box-shadow:0 14px 44px rgba(0,0,0,.3);max-width:min(92vw,420px);opacity:0;transition:transform .38s cubic-bezier(.2,.9,.3,1.25),opacity .3s}'
    + '.cart-toast.show{transform:translate(-50%,0);opacity:1}'
    + '.cart-toast.is-bundle{background:#1a6641}'
    + '.cart-toast-icon{width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;font-size:1.2rem;font-weight:700;flex:none}'
    + '.cart-toast.is-bundle .cart-toast-name{color:rgba(255,255,255,.85)}'
    + '.cart-toast-thumb{width:44px;height:44px;border-radius:8px;object-fit:cover;background:#333;flex:none}'
    + '.cart-toast-body{display:flex;flex-direction:column;line-height:1.25;min-width:0}'
    + '.cart-toast-body strong{font-family:"Space Grotesk",sans-serif;font-size:.9rem}'
    + '.cart-toast-name{font-size:.78rem;color:rgba(255,255,255,.72);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'
    + '.cart-toast-cta{margin-left:auto;flex:none;color:#fff;font-weight:600;font-size:.82rem;text-decoration:none;border-bottom:1px solid rgba(255,255,255,.55);padding-bottom:1px;white-space:nowrap}';
  document.head.appendChild(s);
})();

function _showToast(cfg) {
  let t = document.querySelector('.cart-toast');
  if (!t) { t = document.createElement('div'); t.className = 'cart-toast'; document.body.appendChild(t); }
  t.classList.toggle('is-bundle', !!cfg.bundle);
  const lead = cfg.bundle
    ? '<span class="cart-toast-icon">✓</span>'
    : (cfg.thumb ? '<img class="cart-toast-thumb" src="' + cfg.thumb + '" alt="">' : '');
  t.innerHTML = lead
    + '<div class="cart-toast-body"><strong>' + (cfg.title || '') + '</strong><span class="cart-toast-name">' + (cfg.sub || '') + '</span></div>'
    + '<a class="cart-toast-cta" href="' + (cfg.href || '/order/') + '">' + (cfg.cta || 'View cart →') + '</a>';
  t.classList.remove('show'); void t.offsetWidth; t.classList.add('show');
  clearTimeout(window._cartToastT);
  window._cartToastT = setTimeout(function () { t.classList.remove('show'); }, cfg.bundle ? 4500 : 3500);
}

function showCartToast(name, thumb) {
  _showToast({ title: 'Added to cart', sub: name, thumb: thumb });
}
function showBundleToast() {
  _showToast({ bundle: true, title: 'Bundle unlocked!', sub: '₱998 for 2 — free delivery', cta: 'Checkout →' });
}
window.showCartToast = showCartToast;
window.showBundleToast = showBundleToast;

updateCartBadge();
