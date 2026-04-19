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

  // Best sellers: filter pills + arrow scroll + swatch navigation
  const bsRail = document.querySelector('[data-bs-rail]');
  if (bsRail) {
    const cards = bsRail.querySelectorAll('.bs-card');

    // Swatch definitions per card slug — only the variants we have in the rail
    const SWATCHES = {
      'outback-black':    [{ bg: '#1a1a1a', slug: 'outback-black', active: true  },
                           { bg: '#1e3a5f', slug: 'outback-blue',  active: false }],
      'outback-blue':     [{ bg: '#1a1a1a', slug: 'outback-black', active: false },
                           { bg: '#1e3a5f', slug: 'outback-blue',  active: true  }],
      'rasta-red':        [{ bg: '#c42a2a', slug: 'rasta-red',      active: true  }],
      'bandits-tortoise': [{ bg: 'linear-gradient(135deg,#3a2a1a,#6a4a2a)', slug: 'bandits-tortoise', active: true }],
    };

    const scrollToCard = (slug) => {
      const target = bsRail.querySelector(`.bs-card[href*="slug=${slug}"]`);
      if (!target) return;
      const railRect  = bsRail.getBoundingClientRect();
      const cardRect  = target.getBoundingClientRect();
      const offset    = cardRect.left - railRect.left + bsRail.scrollLeft;
      bsRail.scrollTo({ left: offset, behavior: 'smooth' });
      target.classList.add('swatch-focus');
      setTimeout(() => target.classList.remove('swatch-focus'), 900);
    };

    cards.forEach((card) => {
      const slug = (card.getAttribute('href') || '').match(/slug=([^&"]+)/)?.[1];
      const defs = SWATCHES[slug];
      if (!defs) return;
      const container = card.querySelector('.bs-swatches');
      if (!container) return;

      container.innerHTML = '';
      defs.forEach(({ bg, slug: targetSlug, active }) => {
        const span = document.createElement('span');
        span.className = 'bs-swatch' + (active ? ' is-active' : '');
        span.style.background = bg;
        span.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          scrollToCard(targetSlug);
        });
        container.appendChild(span);
      });
    });

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
