(function (window, document) {
  'use strict';

  var ALLOWED_HOST = 'geralddaquila.com';
  var GENERIC_RATIONALES = [
    'there is something here worth staying with.',
    'this gives you a concrete place to continue with the question you are carrying.',
    'there is something here worth exploring.',
    'this is a useful place to continue.'
  ];
  var LABELS = {
    continue: 'CONTINUE EXPLORING',
    conceptual: 'CONTINUE EXPLORING',
    related: 'CONTINUE EXPLORING'
  };

  function normalizeUrl(rawUrl) {
    if (typeof rawUrl !== 'string' || !rawUrl.trim() || rawUrl.length > 2048) return null;
    if (!/^https:\/\/geralddaquila\\.com(?:\/|$)/i.test(rawUrl.trim())) return null;
    var url;
    try { url = new URL(rawUrl.trim(), window.location.origin); } catch (_) { return null; }
    if (url.protocol !== 'https:' ||
        url.hostname.toLowerCase() !== ALLOWED_HOST ||
        (url.port && url.port !== '443') ||
        url.username || url.password ||
        !url.pathname || url.pathname.charAt(0) !== '/' ||
        url.search || url.hash) return null;
    return url.href;
  }

  function normalize(item) {
    if (!item || typeof item !== 'object') return null;
    var title = typeof item.title === 'string' ? item.title.trim() : '';
    var rationale = typeof item.rationale === 'string' ? item.rationale.trim() : '';
    var rawUrl = typeof item.url === 'string' ? item.url.trim() : '';
    var safeUrl = normalizeUrl(rawUrl);
    if (!title || title.length > 180 || !rationale || rationale.length > 600 || !safeUrl) return null;
    if (GENERIC_RATIONALES.indexOf(rationale.toLowerCase()) !== -1) return null;

    return {
      title: title,
      rationale: rationale,
      url: safeUrl,
      label: LABELS[item.kind] || LABELS.continue
    };
  }

  function build(item) {
    var card = document.createElement('section');
    card.className = 'la-answer-doorway';
    card.setAttribute('aria-label', 'Continue exploring the Living Archive');

    var label = document.createElement('p');
    label.className = 'la-answer-doorway__label';
    label.textContent = item.label;

    var rationale = document.createElement('p');
    rationale.className = 'la-answer-doorway__rationale';
    rationale.textContent = item.rationale;

    var link = document.createElement('a');
    link.className = 'la-answer-doorway__link';
    link.href = item.url;
    link.textContent = item.title;
    link.setAttribute('aria-label', 'Continue exploring: ' + item.title);

    card.appendChild(label);
    card.appendChild(rationale);
    card.appendChild(link);
    return card;
  }

  function render(container, item) {
    if (!container || typeof container.replaceChildren !== 'function') return false;
    var normalized = normalize(item);
    container.replaceChildren();
    if (!normalized) {
      container.hidden = true;
      return false;
    }
    container.appendChild(build(normalized));
    container.hidden = false;
    return true;
  }

  function renderMany(container, items) {
    if (!container || typeof container.replaceChildren !== 'function') return 0;
    container.replaceChildren();
    if (!Array.isArray(items)) {
      container.hidden = true;
      return 0;
    }
    var fragment = document.createDocumentFragment();
    var count = 0;
    items.forEach(function (item) {
      var normalized = normalize(item);
      if (!normalized) return;
      fragment.appendChild(build(normalized));
      count += 1;
    });
    if (count) container.appendChild(fragment);
    container.hidden = count === 0;
    return count;
  }

  window.LivingArchiveAnswerDoorway = Object.freeze({
    version: '1.0.0',
    normalize: normalize,
    normalizeUrl: normalizeUrl,
    render: render,
    renderMany: renderMany
  });
})(window, document);
