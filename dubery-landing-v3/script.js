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
  // Swipe + arrow navigation on best seller cards
  function attachCardSwipe(cards) {
    cards.forEach(card => {
      const dots = card.querySelectorAll('.bs-dot');

      function setSwipe(swiped) {
        card.classList.toggle('is-swiped', swiped);
        dots.forEach((d, i) => d.classList.toggle('active', i === (swiped ? 1 : 0)));
      }

      card.querySelectorAll('.bs-nav').forEach(btn => {
        btn.addEventListener('click', e => {
          e.preventDefault();
          e.stopPropagation();
          setSwipe(btn.classList.contains('bs-nav--next'));
        });
      });

      let startX = 0;
      card.addEventListener('touchstart', e => {
        startX = e.touches[0].clientX;
      }, { passive: true });
      card.addEventListener('touchend', e => {
        const dx = e.changedTouches[0].clientX - startX;
        if (Math.abs(dx) > 40) {
          e.preventDefault();
          setSwipe(dx < 0);
        }
      });
    });
  }
  attachCardSwipe(document.querySelectorAll('.bs-card'));

  // Shop Our Feed teaser — random 12 from shop-social/data.json
  const feedGrid = document.querySelector('[data-feed-grid]');
  if (feedGrid) {
    fetch('shop-social/data.json')
      .then(r => r.json())
      .then(tiles => {
        // Fisher-Yates shuffle, pick first 12
        for (let i = tiles.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [tiles[i], tiles[j]] = [tiles[j], tiles[i]];
        }
        const pick = tiles.slice(0, 12);
        feedGrid.innerHTML = pick.map(t => `
          <a href="shop-social/#tile-${t.id}" class="social-tile">
            <img src="${t.image}" alt="${t.caption}" loading="lazy">
            <span class="social-tag">${t.author}</span>
          </a>
        `).join('');
      })
      .catch(() => {}); // keep existing static tiles on failure
  }
})();
