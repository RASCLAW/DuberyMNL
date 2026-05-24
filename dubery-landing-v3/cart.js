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
