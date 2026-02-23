/**
 * BeJob — Main JS
 * Menu mobile, sticky header, filtres, lazy load, copier lien, back to top
 */
(function () {
  'use strict';

  function getTheme() {
    try { return localStorage.getItem('theme') || 'auto'; } catch (e) { return 'auto'; }
  }

  function setTheme(theme) {
    try { localStorage.setItem('theme', theme); } catch (e) {}
    if (theme && theme !== 'auto') {
      document.documentElement.setAttribute('data-theme', theme);
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
    }
  }

  var themeBtn = document.getElementById('theme-toggle');
  if (themeBtn) {
    setTheme(getTheme());
    themeBtn.addEventListener('click', function () {
      var cur = getTheme();
      var next = cur === 'dark' ? 'light' : 'dark';
      setTheme(next);
    });
  }

  var menuToggle = document.getElementById('menu-toggle');
  var navMain = document.getElementById('nav-main');
  if (menuToggle && navMain) {
    menuToggle.addEventListener('click', function () {
      navMain.classList.toggle('open');
      menuToggle.setAttribute('aria-expanded', navMain.classList.contains('open'));
    });
    document.addEventListener('click', function (e) {
      if (!navMain.contains(e.target) && !menuToggle.contains(e.target)) {
        navMain.classList.remove('open');
        menuToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  if (navMain) {
    navMain.addEventListener('click', function (e) {
      var a = e.target && e.target.closest ? e.target.closest('a[aria-haspopup="true"]') : null;
      if (!a) return;
      if (!window.matchMedia || !window.matchMedia('(max-width: 768px)').matches) return;
      e.preventDefault();
      var li = a.closest('li');
      if (!li) return;
      var open = li.classList.toggle('open');
      a.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  var header = document.getElementById('site-header');
  if (header) {
    window.addEventListener('scroll', function () {
      header.classList.toggle('scrolled', window.scrollY > 60);
    });
  }

  var listCards = document.getElementById('list-cards');
  var pills = document.querySelectorAll('.filter-pill');
  if (listCards && pills.length) {
    pills.forEach(function (pill) {
      pill.addEventListener('click', function () {
        pills.forEach(function (p) { p.classList.remove('active'); });
        pill.classList.add('active');
        var filter = pill.getAttribute('data-filter');
        var cards = listCards.querySelectorAll('.card');
        cards.forEach(function (card) {
          var type = (card.getAttribute('data-type') || '').toLowerCase();
          var show = filter === 'all' || type.indexOf(filter) !== -1;
          card.style.display = show ? '' : 'none';
        });
      });
    });
  }

  document.querySelectorAll('.share-copy').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var url = btn.getAttribute('data-copy-url') || window.location.href;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(function () {
          var t = btn.textContent;
          btn.textContent = 'Copié !';
          setTimeout(function () { btn.textContent = t; }, 2000);
        });
      }
    });
  });

  var searchResults = document.getElementById('search-results');
  var searchInput = document.getElementById('search-input');
  var searchMeta = document.getElementById('search-meta');
  if (searchResults && searchInput) {
    var cache = null;

    function getQuery() {
      try {
        var u = new URL(window.location.href);
        return (u.searchParams.get('q') || '').trim();
      } catch (e) {
        return '';
      }
    }

    function normalize(s) {
      return (s || '')
        .toString()
        .toLowerCase()
        .normalize('NFD')
        .replace(/\p{Diacritic}/gu, '')
        .replace(/[^a-z0-9\s-]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    }

    function render(items, q) {
      searchResults.innerHTML = '';
      if (searchMeta) {
        if (!q) {
          searchMeta.textContent = 'Entrez un mot-clé pour lancer la recherche.';
        } else {
          searchMeta.textContent = items.length + ' résultat(s) pour "' + q + '"';
        }
      }
      if (!q) {
        searchResults.innerHTML = '<div class="search-empty">Exemples: <strong>comptable</strong>, <strong>Casablanca</strong>, <strong>stage</strong>.</div>';
        return;
      }
      if (!items.length) {
        searchResults.innerHTML = '<div class="search-empty">Aucun résultat. Essayez un autre mot-clé.</div>';
        return;
      }
      items.forEach(function (p) {
        var a = document.createElement('a');
        a.className = 'card';
        a.href = p.url;
        a.innerHTML =
          '<h2 class="card-title">' + (p.title || '') + '</h2>' +
          '<span class="card-meta">🏢 ' + (p.company || '—') + ' · 📍 ' + (p.location || '—') + '</span>' +
          '<span class="btn-card">Voir l\'offre →</span>';
        searchResults.appendChild(a);
      });
    }

    function filterPages(pages, q) {
      var nq = normalize(q);
      if (!nq) return [];
      return pages.filter(function (p) {
        var hay = normalize([p.title, p.company, p.location, p.contract_type, p.section, p.description, (p.keywords || []).join(' ')].join(' '));
        return hay.indexOf(nq) !== -1;
      });
    }

    function ensureIndex(cb) {
      if (cache) return cb(null, cache);
      fetch('/index.json', { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          cache = Array.isArray(data) ? data : [];
          cb(null, cache);
        })
        .catch(function (err) { cb(err); });
    }

    function run(q) {
      ensureIndex(function (err, pages) {
        if (err) {
          if (searchMeta) searchMeta.textContent = 'Recherche indisponible pour le moment.';
          return;
        }
        render(filterPages(pages, q), q);
      });
    }

    var initialQ = getQuery();
    if (initialQ) searchInput.value = initialQ;
    run(initialQ);

    var tId = null;
    searchInput.addEventListener('input', function () {
      var q = searchInput.value || '';
      if (tId) clearTimeout(tId);
      tId = setTimeout(function () { run(q); }, 120);
    });
  }

  if ('IntersectionObserver' in window) {
    var imgObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var img = entry.target;
          if (img.dataset.src) { img.src = img.dataset.src; img.removeAttribute('data-src'); }
          imgObserver.unobserve(img);
        }
      });
    }, { rootMargin: '50px' });
    document.querySelectorAll('img[data-src]').forEach(function (img) { imgObserver.observe(img); });
  }

  var backTop = document.createElement('button');
  backTop.className = 'back-to-top';
  backTop.setAttribute('aria-label', 'Retour en haut');
  backTop.textContent = '↑';
  backTop.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;width:44px;height:44px;border-radius:50%;background:var(--primary);color:#fff;border:none;cursor:pointer;display:none;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:50;';
  document.body.appendChild(backTop);
  window.addEventListener('scroll', function () {
    backTop.style.display = window.scrollY > 400 ? 'block' : 'none';
  });
  backTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
})();
