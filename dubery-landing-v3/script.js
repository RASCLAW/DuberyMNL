/* DuberyMNL v3 — minimal interactions
   No framework. Nav toggle + sticky border on scroll.
   ============================================================ */
'use strict';

(function () {
  // Mobile nav toggle
  const toggle = document.querySelector('[data-nav-toggle]');
  const links = document.querySelector('[data-nav-links]');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('is-open');
    });
    // Close menu after clicking an in-page anchor
    links.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', () => links.classList.remove('is-open'));
    });
  }

  // Sticky header border on scroll
  const header = document.querySelector('.site-header');
  if (header) {
    const onScroll = () => {
      header.classList.toggle('is-scrolled', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // Best sellers: filter pills + arrow scroll
  const bsRail = document.querySelector('[data-bs-rail]');
  if (bsRail) {
    const cards = bsRail.querySelectorAll('.bs-card');

    document.querySelectorAll('.bs-filter').forEach((pill) => {
      pill.addEventListener('click', () => {
        const filter = pill.dataset.filter;
        document.querySelectorAll('.bs-filter').forEach((p) => p.classList.remove('is-active'));
        pill.classList.add('is-active');
        cards.forEach((card) => {
          const match = filter === 'all' || card.dataset.series === filter;
          card.hidden = !match;
        });
        bsRail.scrollTo({ left: 0, behavior: 'smooth' });
      });
    });

    const cardStep = () => {
      const first = bsRail.querySelector('.bs-card:not([hidden])');
      if (!first) return bsRail.clientWidth * 0.8;
      const styles = getComputedStyle(bsRail);
      const gap = parseFloat(styles.columnGap || styles.gap || '0');
      return first.getBoundingClientRect().width + gap;
    };
    document.querySelectorAll('.bs-arrow').forEach((arrow) => {
      arrow.addEventListener('click', () => {
        const dir = arrow.dataset.arrow === 'next' ? 1 : -1;
        bsRail.scrollBy({ left: cardStep() * dir, behavior: 'smooth' });
      });
    });
  }
})();
