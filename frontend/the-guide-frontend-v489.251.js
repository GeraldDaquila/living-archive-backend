(function (window, nativeDocument) {
  'use strict';

  function bootGuideWoodyController() {
    var guideRoot = nativeDocument.querySelector('.archive-stage-wrapper[data-guide-instance="woody"]');
    if (!guideRoot) return false;
    if (guideRoot.dataset.useScopedControllerLoaded === '1') return true;
    guideRoot.dataset.useScopedControllerLoaded = '1';
  var document = new Proxy(nativeDocument, {
    get: function (target, property) {
      if (property === 'getElementById') {
        return function (id) {
          var local = guideRoot.querySelector('#' + String(id));
          return local || target.getElementById(id);
        };
      }
      if (property === 'querySelector') {
        return function (selector) {
          return guideRoot.querySelector(selector) || target.querySelector(selector);
        };
      }
      if (property === 'querySelectorAll') {
        return function (selector) {
          var local = guideRoot.querySelectorAll(selector);
          return local.length ? local : target.querySelectorAll(selector);
        };
      }
      var value = Reflect.get(target, property, target);
      return typeof value === 'function' ? value.bind(target) : value;
    }
  });
/* ================================================================
   USE FRONTEND v489.245
   SINGLE CONTROLLER + SAFETY BOUNDARY
   ================================================================ */

var USE_PRIMARY_ENDPOINT =
  'https://living-archive-backend.onrender.com/api/query';

var USE_SECONDARY_ENDPOINT =
  'https://living-archive-backend-mirror.onrender.com/api/query';

/* Controlled acceptance-test target. Never selected for ordinary visitors. */
var USE_PREDICTIVE_SHADOW_ENDPOINT =
  'https://living-archive-predictive-shadow.onrender.com/api/query';

function useGuidePredictiveShadowRequested() {
  try {
    var params = new URLSearchParams(window.location.search || '');
    var requested = params.get('guide_backend') === 'predictive-shadow';
    window.__LIVING_ARCHIVE_GUIDE_BACKEND =
      requested ? 'predictive-shadow' : 'production';
    console.info('[The Guide] backend mode:', window.__LIVING_ARCHIVE_GUIDE_BACKEND);
    return requested;
  } catch (e) {
    window.__LIVING_ARCHIVE_GUIDE_BACKEND = 'production';
    return false;
  }
}

/* Backward-compatible alias: primary remains the authoritative endpoint. */
var USE_API_ENDPOINT = USE_PRIMARY_ENDPOINT;

var USE_TRANSPORT_TIMEOUT_MS = 30000;

var HRN_PAGE_URL =
  'https://geralddaquila.com/understanding-human-systems-behavior-pressure-and-decision-making/';

var USE_FRONTEND_BUILD = 'v489.251-predictive-shadow-explicit';
var USE_FRONTEND_AUTHORITY = 'guide-woody-scoped-controller';
var USE_HRN_HANDOFF_CONTRACT = 'relationship-v2-browser-entrance';

var GUIDE_HINT_EXAMPLES = [
  "Where should I begin with the Living Archive?",
  "What does stewardship mean here?",
  "I keep seeing the same pattern in my organization.",
  "Where can I explore Philippine systems?",
  "What is this symbol?",
  "I want to understand what is happening between us."
];

var guideHintIndex = 0;
var guideHintTimer = null;
var guideConversationHistory = [];
var guideLastRecommendation = null;
var guideOrdinaryFollowupInFlight = false;
var guideSafetyActive = false;
var guideSafetyQuestion = '';
var guideSafetyState = '';
var guideSafetySubmissionInFlight = false;
var guideSafetyLocationRequired = false;
var guideSafetyCountry = '';
var guideSafetyLocationRefused = false;

var guideRequestSequence = 0;
var guideActiveRequestToken = 0;
var guideResponseObserver = null;

function renderGuidePayload(responseText, response, query, token) {
  if (!responseText) throw new Error('The response surface is unavailable.');
  var authoritative = String(response || '').trim();
  if (!authoritative) throw new Error('The Guide returned an empty response.');

  function render() {
    var html;
    try {
      html = (typeof marked !== 'undefined' && marked && typeof marked.parse === 'function')
        ? marked.parse(authoritative)
        : escapeHtml(authoritative).replace(/\r?\n/g, '<br>');
    } catch (e) {
      html = escapeHtml(authoritative).replace(/\r?\n/g, '<br>');
    }
    responseText.innerHTML = html;
    responseText.dataset.guideRequestToken = String(token);
    responseText.dataset.guideResponseQuery = String(query);
    responseText.dataset.guideResponseText = authoritative;
  }

  render();

  if (guideResponseObserver) guideResponseObserver.disconnect();
  if (typeof MutationObserver !== 'undefined') {
    var restoring = false;
    guideResponseObserver = new MutationObserver(function () {
      if (restoring || guideActiveRequestToken !== token) return;
      var visible = String(responseText.innerText || '').trim();
      var expected = String(responseText.dataset.guideResponseText || '').trim();
      var visibleNorm = visible.replace(/\s+/g, ' ');
      var expectedNorm = expected.replace(/\s+/g, ' ');
      // The controller may append a canonical doorway after the answer. Preserve
      // that legitimate continuation while still rejecting a replacement of the
      // authoritative answer itself.
      if (expectedNorm && !visibleNorm.startsWith(expectedNorm)) {
        restoring = true;
        console.error('The Guide payload-integrity boundary restored an overwritten response.', {token: token});
        render();
        restoring = false;
      }
    });
    guideResponseObserver.observe(responseText, {childList:true,subtree:true,characterData:true});
  }
}

/* ================================================================
   QUERY FIELD PRESENTATION + AUTO-GROW
   ================================================================
   This controller owns only the main Guide query field. It reinforces the
   18px presentation at runtime and grows the field with wrapped content.
   The field remains bounded so a long question does not consume the page.
*/

function applyGuideQueryFieldPresentation() {

  var input = document.getElementById('archive-query-input');

  if (!input) return;

  input.style.setProperty('font-size', '19px', 'important');
  input.style.setProperty('line-height', '1.55', 'important');
  input.style.setProperty('font-weight', '400', 'important');
  input.style.setProperty('max-height', '300px', 'important');
  input.style.setProperty('box-sizing', 'border-box', 'important');
}

function resizeGuideQueryInput() {

  var input = document.getElementById('archive-query-input');

  if (!input) return;

  var maxHeight = 300;

  input.style.setProperty('height', 'auto', 'important');

  var targetHeight = Math.max(
    120,
    Math.min(input.scrollHeight, maxHeight)
  );

  input.style.setProperty(
    'height',
    targetHeight + 'px',
    'important'
  );

  input.style.setProperty(
    'overflow-y',
    input.scrollHeight > maxHeight ? 'auto' : 'hidden',
    'important'
  );
}

function initializeGuideQueryField() {

  var input = document.getElementById('archive-query-input');

  if (!input || input.dataset.useQueryFieldInitialized === '1') return;

  input.dataset.useQueryFieldInitialized = '1';

  applyGuideQueryFieldPresentation();
  resizeGuideQueryInput();

  input.addEventListener('input', resizeGuideQueryInput);
  input.addEventListener('change', resizeGuideQueryInput);

  window.addEventListener('resize', resizeGuideQueryInput);
}

/* ================================================================
   HINT ROTATION
   ================================================================ */

function setGuideHint(index, animate) {

  var input = document.getElementById('archive-query-input');

  if (!input) return;
  if (input.value.trim()) return;

  guideHintIndex =
    ((index % GUIDE_HINT_EXAMPLES.length) +
      GUIDE_HINT_EXAMPLES.length) %
    GUIDE_HINT_EXAMPLES.length;

  var nextHint = GUIDE_HINT_EXAMPLES[guideHintIndex];

  var reduceMotion =
    window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!animate || reduceMotion) {

    input.classList.remove('guide-hint-fading');
    input.classList.add('guide-hint-ready');
    input.placeholder = nextHint;

    return;
  }

  input.classList.remove('guide-hint-ready');
  input.classList.add('guide-hint-fading');

  window.setTimeout(function () {

    var currentInput =
      document.getElementById('archive-query-input');

    if (!currentInput || currentInput.value.trim()) return;

    currentInput.placeholder = nextHint;

    window.requestAnimationFrame(function () {

      currentInput.classList.remove('guide-hint-fading');
      currentInput.classList.add('guide-hint-ready');

    });

  }, 320);
}

function startGuideHintRotation() {

  if (guideHintTimer) {
    clearInterval(guideHintTimer);
  }

  setGuideHint(guideHintIndex);

  guideHintTimer = setInterval(function () {

    var input =
      document.getElementById('archive-query-input');

    if (
      !input ||
      input.value.trim() ||
      document.activeElement === input
    ) {
      return;
    }

    setGuideHint(guideHintIndex + 1, true);

  }, 4500);
}

function stopGuideHintRotation() {

  if (guideHintTimer) {
    clearInterval(guideHintTimer);
    guideHintTimer = null;
  }
}

function initializeGuideHints() {

  initializeGuideQueryField();

  var input =
    document.getElementById('archive-query-input');

  if (!input) return;

  input.placeholder =
    GUIDE_HINT_EXAMPLES[guideHintIndex];

  input.addEventListener('focus', function () {
    stopGuideHintRotation();
  });

  input.addEventListener('blur', function () {

    if (!input.value.trim()) {
      startGuideHintRotation();
    }

  });

  startGuideHintRotation();
}

/* ================================================================
   ESCAPING
   ================================================================ */

function escapeHtml(value) {

  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

}

/* ================================================================
   VISITOR-LANGUAGE RESPONSE BOUNDARY
   ================================================================
   The backend is authoritative for visitor-language composition.
   The browser adds defense in depth: known implementation metadata must
   never be rendered even if a stale/malformed backend response escapes.
   This is a rejection boundary, not a rewriting layer.
*/

function hasInternalGuideLanguage(value) {

  var text = String(value || '');

  return /(?:\[\s*(?:evidence excerpt|canonical evidence|supplied evidence|internal interpretation|retrieval|synthesis|processing layer|provider|model|route|handoff)\s*\]|evidence excerpt bounded by USE|canonical evidence|supplied evidence|internal interpretation|bounded by USE|processing layer|retrieval layer|synthesis layer|machine-facing|implementation metadata)/i.test(text);

}

function assertVisitorLanguageBoundary(data) {

  if (!data || typeof data !== 'object') {
    throw new Error('Invalid Guide response envelope');
  }

  var response = String(data.response || '').trim();

  if (response && hasInternalGuideLanguage(response)) {
    console.error(
      'The Guide visitor-language boundary rejected internal response metadata.'
    );

    throw new Error(
      'Guide response failed visitor-language boundary'
    );
  }

  return data;

}

/* ================================================================
   USE TRANSPORT / FAILOVER
   Primary remains first. Secondary is tried after transport/server
   failures or explicit retryable application failures. Valid answers,
   safety responses, and specialist handoffs are never silently retried.
   ================================================================ */

function useTransportRetryableStatus(status) {

  return (
    status === 500 ||
    status === 502 ||
    status === 503 ||
    status === 504 ||
    status === 522 ||
    status === 524
  );
}

async function fetchUSEEndpoint(endpoint, payload) {

  var controller =
    typeof AbortController !== 'undefined'
      ? new AbortController()
      : null;

  var timeoutId =
    controller
      ? setTimeout(function () {
          controller.abort();
        }, USE_TRANSPORT_TIMEOUT_MS)
      : null;

  try {

    return await fetch(
      endpoint,
      {
        method: 'POST',
        headers: {
          'Content-Type':
            'application/json'
        },
        body: JSON.stringify(payload),
        signal: controller
          ? controller.signal
          : undefined
      }
    );

  } finally {

    if (timeoutId) {
      clearTimeout(timeoutId);
    }

  }
}

async function useGuideApplicationFailureReason(response) {
  if (!response || !response.ok || typeof response.clone !== 'function') return '';
  try {
    var data = await response.clone().json();
    if (!data || typeof data !== 'object') return '';
    // Never retry an authoritative safety response or a specialist handoff.
    if (
      data.intent === 'SAFETY_INTERRUPT' ||
      data.safety_message ||
      data.safety_question ||
      /_HANDOFF$/.test(String(data.intent || ''))
    ) return '';
    if (data.error_type === 'application_generation_failure') {
      return 'application_generation_failure';
    }
    if (
      data.answer_basis &&
      data.answer_basis.kind === 'answer_integrity_failure'
    ) {
      return 'answer_integrity_failure';
    }
    return data.retryable === true ? 'retryable_application_failure' : '';
  } catch (e) {
    return '';
  }
}

async function fetchUSE(payload, requestLabel) {

  var shadowTest = useGuidePredictiveShadowRequested();

  var attempts = shadowTest
    ? [
        {
          name: 'predictive-shadow',
          endpoint: USE_PREDICTIVE_SHADOW_ENDPOINT
        }
      ]
    : [
        {
          name: 'primary',
          endpoint: USE_PRIMARY_ENDPOINT
        },
        {
          name: 'secondary',
          endpoint: USE_SECONDARY_ENDPOINT
        }
      ];

  if (shadowTest) {
    console.info(
      'The Guide controlled acceptance test: predictive shadow selected; production fallback disabled.',
      { request: requestLabel || 'query' }
    );
  }

  var failures = [];

  for (var i = 0; i < attempts.length; i++) {

    var attempt = attempts[i];

    try {

      var response =
        await fetchUSEEndpoint(
          attempt.endpoint,
          payload
        );

      if (response.ok) {
        var applicationFailure =
          await useGuideApplicationFailureReason(response);

        if (applicationFailure) {
          failures.push({
            endpoint: attempt.name,
            reason: applicationFailure
          });

          console.warn(
            'The Guide USE transport: retryable application failure; trying next endpoint',
            {
              request: requestLabel || 'query',
              endpoint: attempt.name,
              reason: applicationFailure
            }
          );

          continue;
        }

        if (attempt.name === 'secondary') {
          console.info(
            'The Guide USE transport: secondary served request',
            {
              request: requestLabel || 'query',
              primary_failures: failures
            }
          );
        }

        return response;
      }

      if (
        !useTransportRetryableStatus(
          response.status
        )
      ) {

        return response;
      }

      failures.push({
        endpoint: attempt.name,
        status: response.status
      });

      console.warn(
        'The Guide USE transport: server failure; trying next endpoint',
        {
          request: requestLabel || 'query',
          endpoint: attempt.name,
          status: response.status
        }
      );

    } catch (error) {

      failures.push({
        endpoint: attempt.name,
        error: error && error.name
          ? error.name
          : 'network_error'
      });

      console.warn(
        'The Guide USE transport: endpoint unavailable; trying next endpoint',
        {
          request: requestLabel || 'query',
          endpoint: attempt.name,
          error: error && error.name
            ? error.name
            : 'network_error'
        }
      );

    }
  }

  var failure =
    new Error(
      'All Living Archive USE endpoints are unavailable.'
    );

  failure.useTransportFailures = failures;
  throw failure;
}

/* ================================================================
   SAFETY BOUNDARY
   ================================================================ */

/*
 * Safety is authoritative if the backend explicitly declares
 * SAFETY_INTERRUPT OR supplies an authoritative safety payload.
 *
 * This is deliberately fail-closed.
 *
 * A malformed response containing safety material must never fall
 * through into ordinary USE rendering.
 */

function hasAuthoritativeSafetyPayload(data) {

  if (!data || typeof data !== 'object') {
    return false;
  }

  if (data.intent === 'SAFETY_INTERRUPT') {
    return true;
  }

  if (
    typeof data.safety_message === 'string' &&
    data.safety_message.trim()
  ) {
    return true;
  }

  if (
    typeof data.safety_question === 'string' &&
    data.safety_question.trim()
  ) {
    return true;
  }

  if (
    Array.isArray(data.safety_resources) &&
    data.safety_resources.length
  ) {
    return true;
  }

  return false;
}

function naturalizeSafetyMessage(message, isInitialTurn) {

  var text =
    String(message || '').trim();

  if (
    isInitialTurn &&
    /taking your [“"]yes[”"] seriously/i.test(text)
  ) {

    return 'Thank you for telling me. I want to take what you just said seriously.';

  }

  return text;
}

/* ================================================================
   SAFETY RESOURCES
   ================================================================ */

function renderSafetyResources(resources) {

  if (
    !Array.isArray(resources) ||
    !resources.length
  ) {
    return '';
  }

  var cards = resources.map(function (resource) {

    if (
      !resource ||
      typeof resource !== 'object'
    ) {
      return '';
    }

    var title =
      String(
        resource.title ||
        resource.display_name ||
        'Emergency or crisis support'
      ).trim();

    var phone =
      String(
        resource.phone ||
        resource.number ||
        ''
      ).trim();

    var url =
      String(
        resource.url ||
        resource.website ||
        ''
      ).trim();

    var contact = '';

    if (phone) {

      contact =
        '<a class="safety-resource-phone" href="tel:' +
        encodeURIComponent(phone) +
        '">' +
        '<span class="safety-call-label">CALL:</span>' +
        escapeHtml(phone) +
        '</a>';

    } else if (
      url &&
      /^https?:\/\//i.test(url)
    ) {

      contact =
        '<a class="safety-resource-phone" href="' +
        escapeHtml(url) +
        '" target="_blank" rel="noopener noreferrer">' +
        'Open support' +
        '</a>';

    }

    return (
      '<div class="safety-resource-card">' +
        '<div class="safety-resource-title">' +
          escapeHtml(title) +
        '</div>' +
        contact +
      '</div>'
    );

  }).join('');

  return cards
    ? '<div class="safety-resources">' +
        '<div class="safety-resources-title">Immediate help</div>' +
        cards +
      '</div>'
    : '';
}

/* ================================================================
   SAFETY FOLLOW-UP
   ================================================================ */

function setSafetyFollowupVisible(
  question,
  enabled
) {

  var wrapper =
    document.getElementById(
      'archive-safety-followup'
    );

  var questionEl =
    document.getElementById(
      'archive-safety-question'
    );

  var input =
    document.getElementById(
      'archive-safety-input'
    );

  var controls =
    document.getElementById(
      'archive-response-controls'
    );

  var container =
    document.getElementById(
      'archive-container-top'
    );

  if (
    !wrapper ||
    !questionEl ||
    !input
  ) {
    return;
  }

  if (
    !enabled ||
    !String(question || '').trim()
  ) {

    wrapper.style.display = 'none';

    if (container) {
      container.classList.remove(
        'archive-safety-active'
      );
    }

    if (controls) {
      controls.style.display = 'none';
    }

    guideSafetyQuestion = '';
    guideSafetyState = '';

    return;
  }

  questionEl.textContent =
    String(question).trim();

  input.value = '';
  input.disabled = false;

  wrapper.style.display = 'block';

  if (container) {
    container.classList.add(
      'archive-safety-active'
    );
  }

  if (controls) {
    controls.style.display = 'none';
  }

  window.setTimeout(function () {
    input.focus();
  }, 100);
}

function syncSafetyLocationFields() {

  var wrapper = document.getElementById('archive-safety-followup');
  var input = document.getElementById('archive-safety-input');
  if (!wrapper || !input) return;

  var existing = document.getElementById('archive-safety-location-fields');

  if (!guideSafetyLocationRequired) {
    if (existing) existing.remove();
    guideSafetyCountry = '';
    guideSafetyLocationRefused = false;
    return;
  }

  if (!existing) {
    existing = document.createElement('div');
    existing.id = 'archive-safety-location-fields';
    existing.style.margin = '0 0 12px';
    existing.style.padding = '12px 14px';
    existing.style.border = '1px solid #cfcfcf';
    existing.style.borderRadius = '12px';
    existing.style.background = '#fff';

    var label = document.createElement('label');
    label.htmlFor = 'archive-safety-country';
    label.textContent = 'To find a verified local emergency contact, what country are you in?';
    label.style.display = 'block';
    label.style.marginBottom = '8px';
    label.style.fontSize = '15px';
    label.style.lineHeight = '1.45';
    label.style.fontWeight = '600';
    label.style.color = '#222';

    var countryInput = document.createElement('input');
    countryInput.type = 'text';
    countryInput.id = 'archive-safety-country';
    countryInput.autocomplete = 'country-name';
    countryInput.placeholder = 'Country (optional)';
    countryInput.value = guideSafetyCountry;
    countryInput.style.display = 'block';
    countryInput.style.width = '100%';
    countryInput.style.boxSizing = 'border-box';
    countryInput.style.minHeight = '44px';
    countryInput.style.padding = '10px 12px';
    countryInput.style.border = '1px solid #cfcfcf';
    countryInput.style.borderRadius = '10px';
    countryInput.style.background = '#fff';
    countryInput.style.color = '#222';
    countryInput.style.font = 'inherit';
    countryInput.addEventListener('input', function() {
      guideSafetyCountry = countryInput.value.trim();
      if (guideSafetyCountry) {
        guideSafetyLocationRefused = false;
        var refusal = document.getElementById('archive-safety-location-refused');
        if (refusal) refusal.checked = false;
      }
    });

    var refusalLabel = document.createElement('label');
    refusalLabel.style.display = 'flex';
    refusalLabel.style.alignItems = 'flex-start';
    refusalLabel.style.gap = '8px';
    refusalLabel.style.marginTop = '10px';
    refusalLabel.style.fontSize = '14px';
    refusalLabel.style.lineHeight = '1.4';
    refusalLabel.style.color = '#444';

    var refusal = document.createElement('input');
    refusal.type = 'checkbox';
    refusal.id = 'archive-safety-location-refused';
    refusal.checked = guideSafetyLocationRefused;
    refusal.style.marginTop = '3px';
    refusal.addEventListener('change', function() {
      guideSafetyLocationRefused = refusal.checked;
      countryInput.disabled = refusal.checked;
      if (refusal.checked) {
        countryInput.value = '';
        guideSafetyCountry = '';
      }
    });

    var refusalText = document.createElement('span');
    refusalText.textContent = 'I’d rather not share my country.';
    refusalLabel.appendChild(refusal);
    refusalLabel.appendChild(refusalText);

    existing.appendChild(label);
    existing.appendChild(countryInput);
    existing.appendChild(refusalLabel);
    wrapper.insertBefore(existing, input);
  } else {
    var existingCountry = document.getElementById('archive-safety-country');
    var existingRefusal = document.getElementById('archive-safety-location-refused');
    if (existingCountry) existingCountry.value = guideSafetyCountry;
    if (existingRefusal) existingRefusal.checked = guideSafetyLocationRefused;
    if (existingCountry) existingCountry.disabled = guideSafetyLocationRefused;
  }
}

/* ================================================================
   SAFETY RESPONSE
   ================================================================ */

function renderSafetyResponse(data) {

  var responseText =
    document.getElementById(
      'archive-response-text'
    );

  var responseBox =
    document.getElementById(
      'archive-response-box'
    );

  var submitBtn =
    document.getElementById(
      'archive-submit-btn'
    );

  var responseControls =
    document.getElementById(
      'archive-response-controls'
    );

  if (!responseText) return;

  var visitorTurnCount =
    guideConversationHistory.filter(
      function (item) {

        return (
          item &&
          item.role === 'visitor'
        );

      }
    ).length;

  var isInitialTurn =
    visitorTurnCount === 1;

  var message =
    naturalizeSafetyMessage(
      data && data.safety_message
        ? data.safety_message
        : (
            data
              ? data.response
              : ''
          ),
      isInitialTurn
    );

  var question =
    String(
      data &&
      data.safety_question
        ? data.safety_question
        : ''
    ).trim();

  /*
   * Fail-closed continuity: an active SAFETY_INTERRUPT is never released
   * merely because a specialist response omitted its next question. The
   * backend owns the primary repair, but the browser boundary must provide
   * the same defense in depth so a transient/malformed specialist response
   * cannot strand the visitor inside a dead safety card.
   */
  var safetyReleaseReady = Boolean(
    data &&
    data.safety_release_ready
  );

  if (
    hasAuthoritativeSafetyPayload(data) &&
    !safetyReleaseReady &&
    !question
  ) {
    /*
     * The backend Safety Intelligence layer is the owner of the next
     * movement. The browser must never restart the safety sequence with a
     * generic opening question merely because a malformed envelope omitted
     * the explicit question. Prefer the server's structured next movement,
     * then the continuity contract, then the still-active prior question as
     * the last safe browser-level hold. This keeps the UI from inventing a
     * second safety state machine.
     */
    question = String(
      data && data.safety && data.safety.next_movement
        ? data.safety.next_movement
        : (data && data.next_movement ? data.next_movement : '')
    ).trim();

    if (!question && guideSafetyQuestion) {
      question = guideSafetyQuestion;
    }
  }

  guideSafetyQuestion = question;
  guideSafetyLocationRequired = Boolean(data && data.safety_location_required);
  guideSafetyState = String(
    data && data.safety && data.safety.state
      ? data.safety.state
      : (data && data.safety_state ? data.safety_state : '')
  ).trim();

  var note =
    String(
      data &&
      data.safety_note
        ? data.safety_note
        : ''
    ).trim();

  var resources =
    data &&
    Array.isArray(data.safety_resources)
      ? data.safety_resources
      : [];

  responseText.innerHTML =
    '<p>' +
      escapeHtml(message)
        .replace(/\n/g, '<br>') +
    '</p>' +
    (
      note
        ? '<div class="safety-note">' +
            escapeHtml(note) +
          '</div>'
        : ''
    );

  if (responseBox) {
    responseBox.style.display = 'block';
  }

  guideSafetyActive =
    Boolean(
      hasAuthoritativeSafetyPayload(data) &&
      !safetyReleaseReady
    );

  setSafetyFollowupVisible(
    question,
    guideSafetyActive
  );
  syncSafetyLocationFields();

  var resourceBox =
    document.getElementById(
      'archive-safety-resources'
    );

  if (resourceBox) {

    resourceBox.innerHTML =
      resources.length
        ? renderSafetyResources(resources)
        : '';

    resourceBox.style.display =
      resources.length
        ? 'block'
        : 'none';
  }

  var mainInput =
    document.getElementById(
      'archive-query-input'
    );

  if (submitBtn) {

    submitBtn.disabled =
      guideSafetyActive;

    submitBtn.classList.remove(
      'is-loading'
    );
  }

  if (mainInput) {

    mainInput.disabled =
      guideSafetyActive;

    mainInput.setAttribute(
      'aria-readonly',
      guideSafetyActive
        ? 'true'
        : 'false'
    );
  }

  if (responseControls) {
    responseControls.style.display = 'none';
  }
}

/* ================================================================
   SAFETY FOLLOW-UP SUBMISSION
   ================================================================ */

async function submitSafetyFollowup() {

  var input =
    document.getElementById(
      'archive-safety-input'
    );

  var button =
    document.getElementById(
      'archive-safety-submit-btn'
    );

  var responseText =
    document.getElementById(
      'archive-response-text'
    );

  if (!input || !button) return;
  if (guideSafetySubmissionInFlight) return;

  var answer =
    input.value.trim();

  if (!answer) {
    input.focus();
    return;
  }

  guideSafetySubmissionInFlight = true;
  button.disabled = true;

  button.classList.add(
    'is-loading'
  );

  guideConversationHistory.push({
    role: 'visitor',
    content: answer
  });

  var countryValue = guideSafetyLocationRefused ? '' : String(guideSafetyCountry || '').trim();
  var safetyLocation = guideSafetyLocationRefused
    ? { refused: true }
    : (countryValue ? { explicit_country: countryValue } : {});

  try {

    var res =
      await fetchUSE(
        {
          query: answer,
          history:
            guideConversationHistory,
          safety_active: true,
          safety_question: guideSafetyQuestion,
          safety_state: guideSafetyState,
          country: countryValue,
          explicit_country: countryValue,
          refused: guideSafetyLocationRefused,
          location: safetyLocation
        },
        'safety-followup'
      );

    if (!res.ok) {
      throw new Error(
        'HTTP status ' +
        res.status
      );
    }

    var data =
      await res.json();

    /*
     * Safety remains authoritative on
     * every follow-up turn.
     */

    if (
      hasAuthoritativeSafetyPayload(data)
    ) {

      guideConversationHistory.push({
        role: 'assistant',
        content:
          data.safety_message ||
          data.response ||
          '',
        question:
          data.safety_question ||
          ''
      });

      renderSafetyResponse(data);

      return;
    }

    /*
     * A follow-up submitted from an active safety lane must never fall into
     * ordinary Guide processing merely because the response envelope is
     * malformed. The safety boundary is already active in this browser
     * session; preserve that state and ask the deterministic opening safety
     * question again rather than manufacturing an ordinary acknowledgement.
     */
    if (guideSafetyActive) {
      var continuityData = {
        intent: 'SAFETY_INTERRUPT',
        safety_message: 'I want to stay with what you just told me.',
        safety_question: guideSafetyQuestion || '',
        safety_state: guideSafetyState || 'acute_followthrough',
        safety_release_ready: false,
        safety_resources: []
      };
      guideConversationHistory.push({
        role: 'assistant',
        content: continuityData.safety_message,
        question: continuityData.safety_question
      });
      renderSafetyResponse(continuityData);
      return;
    }

    guideSafetyActive = false;

    setSafetyFollowupVisible(
      '',
      false
    );

    if (responseText) {

      responseText.innerHTML =
        '<p>' +
        escapeHtml(
          data && data.response
            ? data.response
            : 'Thank you. You can take the next step in your own time.'
        ) +
        '</p>';
    }

  } catch (error) {

    guideConversationHistory.pop();

    if (responseText) {

      responseText.innerHTML =
        "<p style='color: #b91c1c;'>" +
        "I couldn't get your response through just now. Please try again." +
        "</p>";
    }

  } finally {

    guideSafetySubmissionInFlight = false;
    button.disabled = false;

    button.classList.remove(
      'is-loading'
    );

    if (guideSafetyActive) {

      window.setTimeout(
        function () {

          var currentInput =
            document.getElementById(
              'archive-safety-input'
            );

          if (currentInput) {
            currentInput.focus();
          }

        },
        50
      );
    }
  }
}

/* ================================================================
   SAFETY CONTROLLER
   ================================================================ */

function installSafetyFollowupController() {

  if (
    guideRoot.__USE_SAFETY_FOLLOWUP_CONTROLLER__ &&
    window.__USE_SAFETY_FOLLOWUP_CONTROLLER__.build ===
      USE_FRONTEND_BUILD
  ) {
    return;
  }

  var button =
    document.getElementById(
      'archive-safety-submit-btn'
    );

  var input =
    document.getElementById(
      'archive-safety-input'
    );

  if (!button || !input) return;

  /*
   * Purge listeners left by an older Woody copy. Cloning the two interactive
   * nodes preserves their IDs/attributes while removing stale handlers that
   * cannot otherwise be cancelled from a later script instance.
   */
  var cleanButton = button.cloneNode(true);
  var cleanInput = input.cloneNode(true);

  button.parentNode.replaceChild(
    cleanButton,
    button
  );

  input.parentNode.replaceChild(
    cleanInput,
    input
  );

  button = cleanButton;
  input = cleanInput;

  button.addEventListener(
    'click',
    function (event) {
      event.preventDefault();
      event.stopImmediatePropagation();
      submitSafetyFollowup();
    },
    true
  );

  input.addEventListener(
    'keydown',
    function (event) {

      if (
        event.key === 'Enter' &&
        (
          event.ctrlKey ||
          event.metaKey
        )
      ) {

        event.preventDefault();
        event.stopImmediatePropagation();

        submitSafetyFollowup();
      }

    },
    true
  );

  window.__USE_SAFETY_FOLLOWUP_CONTROLLER__ = {
    build: USE_FRONTEND_BUILD,
    installed: true
  };
}

/* ================================================================
   RESPONSE CONTROL
   ================================================================ */

function renderAuthoritativeRecommendation(data) {
  /*
   * Keep the most recent valid canonical doorway across ordinary follow-up
   * turns. The API may correctly omit a new recommendation for a conversational
   * continuation; that must not erase the visitor's existing working link.
   */
  var responseText = document.getElementById('archive-response-text');
  var container = document.getElementById('archive-recommendation');

  var recommendation =
    data &&
    data.recommendation &&
    typeof data.recommendation === 'object'
      ? data.recommendation
      : null;

  var title = recommendation && typeof recommendation.title === 'string'
    ? recommendation.title.trim()
    : '';

  title = title
    .replace(/^[\s\p{Extended_Pictographic}\u{2600}-\u{27BF}]+/u, '')
    .replace(/&amp;/gi, '&')
    .trim();

  var url = recommendation && typeof recommendation.url === 'string'
    ? recommendation.url.trim()
    : '';

  var validCurrentRecommendation =
    !!title && /^https:\/\/geralddaquila\.com\/\S+$/i.test(url);

  if (validCurrentRecommendation) {
    guideLastRecommendation = { title: title, url: url };
  } else if (guideLastRecommendation &&
             typeof guideLastRecommendation.title === 'string' &&
             /^https:\/\/geralddaquila\.com\/\S+$/i.test(guideLastRecommendation.url)) {
    title = guideLastRecommendation.title;
    url = guideLastRecommendation.url;
  } else {
    console.warn('The Guide recommendation was not rendered because no valid canonical recommendation is available.', {
      hasRecommendation: !!recommendation,
      hasTitle: !!title,
      hasUrl: !!url
    });
    return;
  }

  if (container) {
    container.innerHTML = '';
    container.style.display = 'none';
  }

  if (responseText) {
    var prior = responseText.querySelector('.archive-inline-recommendation');
    if (prior) prior.remove();
  }

  var block = document.createElement('div');
  block.className = 'archive-inline-recommendation';
  block.setAttribute('aria-live', 'polite');

  var label = document.createElement('p');
  label.className = 'archive-recommendation-label';
  label.textContent = 'A useful place to continue:';

  var link = document.createElement('a');
  link.className = 'archive-recommendation-link';
  link.href = url;
  link.textContent = title;
  link.setAttribute('aria-label', 'Explore ' + title + ' in the Living Archive');

  block.appendChild(label);
  block.appendChild(link);

  if (responseText) {
    responseText.appendChild(block);
    console.info('The Guide recommendation rendered with canonical URL.', {
      title: title,
      url: url,
      retained_from_prior_turn: !validCurrentRecommendation,
      build: USE_FRONTEND_BUILD
    });
  } else if (container) {
    container.appendChild(block);
    container.style.display = 'block';
  }
}

function configureResponseControl(
  responseTextValue
) {

  var controls =
    document.getElementById(
      'archive-response-controls'
    );

  var button =
    controls
      ? controls.querySelector(
          '.reset-btn'
        )
      : null;

  var icon =
    document.getElementById(
      'archive-response-control-icon'
    );

  var label =
    document.getElementById(
      'archive-response-control-label'
    );

  if (
    !button ||
    !icon ||
    !label
  ) {
    return;
  }

  button.classList.remove(
    'continue-inquiry'
  );

  button.setAttribute(
    'data-response-mode',
    'reset'
  );

  icon.textContent = '↺';

  label.textContent =
    'Start another question';
}

function resetGuideConversationHistory() {

  guideConversationHistory = [];

  guideSafetyActive = false;
  guideSafetyQuestion = '';
  guideSafetyState = '';
  guideSafetySubmissionInFlight = false;
  guideSafetyLocationRequired = false;
  guideSafetyCountry = '';
  guideSafetyLocationRefused = false;
}

function handleResponseControl() {

  resetArchiveSearch();
}

/* ================================================================
   ORDINARY CONVERSATION CONTINUITY
   A visible reply surface accompanies ordinary Guide invitations.
   Safety remains authoritative and is delegated to the existing
   safety renderer whenever the backend returns a safety payload.
   ================================================================ */

function installOrdinaryFollowupStyles() {
  if (document.getElementById('archive-ordinary-followup-styles')) return;
  var style = document.createElement('style');
  style.id = 'archive-ordinary-followup-styles';
  style.textContent = [
    '.archive-ordinary-followup{margin-top:18px;padding-top:16px;border-top:1px solid #d6d6d6;}',
    '.archive-ordinary-followup-label{display:block;margin:0 0 8px;color:#444;font-size:15px;font-weight:600;line-height:1.4;}',
    '.archive-ordinary-followup textarea,.archive-ordinary-followup textarea:hover,.archive-ordinary-followup textarea:active{display:block!important;width:100%!important;max-width:100%!important;min-height:88px!important;box-sizing:border-box!important;padding:12px 14px!important;border:1px solid #cfcfcf!important;border-radius:12px!important;background:#fff!important;color:#222!important;font:inherit!important;font-size:17px!important;line-height:1.5!important;resize:vertical!important;outline:none!important;box-shadow:none!important;-webkit-appearance:none!important;appearance:none!important;}',
    '.archive-ordinary-followup textarea:focus,.archive-ordinary-followup textarea:focus-visible{border:1px solid #bdbdbd!important;outline:0!important;outline-offset:0!important;box-shadow:none!important;}',
    '.archive-ordinary-followup-actions{display:flex;justify-content:flex-end;margin-top:10px;}',
    '.archive-ordinary-followup button{min-width:100px;min-height:44px;border:0;border-radius:12px;padding:10px 18px;background:#000;color:#fff;font:inherit;font-size:16px;cursor:pointer;}',
    '.archive-ordinary-followup button:disabled{opacity:.7;cursor:wait;}',
    '.archive-ordinary-followup-status{margin-top:8px;color:#555;font-size:14px;line-height:1.4;}'
  ].join('');
  document.head.appendChild(style);
}

function renderOrdinaryFollowupPanel(response) {
  var responseText = document.getElementById('archive-response-text');
  if (!responseText || guideSafetyActive) return;
  var existing = document.getElementById('archive-ordinary-followup');
  if (existing) existing.remove();

  /*
   * A reply field belongs to an actual conversational invitation.
   * Do not add a permanent second search box beneath every answer.
   */
  var finalText = String(response || '').trim();
  var invitesReply = /\?\s*[”’"'\])}]*$/.test(finalText);
  if (!invitesReply) return;

  installOrdinaryFollowupStyles();

  var panel = document.createElement('form');
  panel.id = 'archive-ordinary-followup';
  panel.className = 'archive-ordinary-followup';
  panel.setAttribute('aria-label', 'Continue this conversation');

  var label = document.createElement('label');
  label.className = 'archive-ordinary-followup-label';
  label.setAttribute('for', 'archive-ordinary-followup-input');
  label.textContent = 'If you’d like to say more, you can reply here.';

  var input = document.createElement('textarea');
  input.id = 'archive-ordinary-followup-input';
  input.rows = 3;
  input.placeholder = 'Write your reply or ask a follow-up question…';
  input.setAttribute('aria-label', 'Your reply to The Guide');
  input.setAttribute('autocomplete', 'off');

  var actions = document.createElement('div');
  actions.className = 'archive-ordinary-followup-actions';
  var button = document.createElement('button');
  button.type = 'submit';
  button.id = 'archive-ordinary-followup-submit';
  button.textContent = 'Reply';
  actions.appendChild(button);

  var status = document.createElement('div');
  status.className = 'archive-ordinary-followup-status';
  status.id = 'archive-ordinary-followup-status';
  status.setAttribute('aria-live', 'polite');

  panel.appendChild(label);
  panel.appendChild(input);
  panel.appendChild(actions);
  panel.appendChild(status);
  responseText.appendChild(panel);

  panel.addEventListener('submit', function(event) {
    event.preventDefault();
    submitOrdinaryFollowup(panel, input, button, status);
  });
}

async function submitOrdinaryFollowup(panel, input, button, status) {
  if (guideOrdinaryFollowupInFlight) return;
  var answer = String(input.value || '').trim();
  if (!answer) { input.focus(); return; }

  guideOrdinaryFollowupInFlight = true;
  button.disabled = true;
  button.textContent = 'Sending…';
  status.textContent = 'The Guide is considering your reply…';
  guideConversationHistory.push({ role: 'visitor', content: answer });

  try {
    var res = await fetchUSE({
      query: answer,
      history: guideConversationHistory,
      conversation_continuation: true
    }, 'guide-followup');

    if (!res.ok) throw new Error('HTTP status ' + res.status);
    var data = await res.json();

    if (hasAuthoritativeSafetyPayload(data)) {
      guideConversationHistory.push({
        role: 'assistant',
        content: data.safety_message || data.response || '',
        question: data.safety_question || ''
      });
      renderSafetyResponse(data);
      return;
    }

    if (data && data.intent === 'RELATIONAL_HANDOFF' && data.relational_delegation) {
      var delegation = data.relational_delegation;
      window.location.assign(HRN_PAGE_URL + '?hrn_seed=' +
        encodeURIComponent(delegation.seed_message || answer) +
        '&hrn_session=' + encodeURIComponent(delegation.session_id || ''));
      return;
    }

    var handoffs = [
      ['GLOSSARY_HANDOFF','glossary_url'],
      ['CATALOGUE_HANDOFF','catalogue_url'],
      ['ATLAS_HANDOFF','atlas_url'],
      ['GUIDE_NODE_HANDOFF','guide_node_url'],
      ['NAVIGATOR_HANDOFF','navigator_url'],
      ['GLYPH_HANDOFF','glyph_url'],
      ['SYSTEMS_PH_HANDOFF','philippine_systems_url'],
      ['FSD_HANDOFF','fsd_url']
    ];
    for (var i = 0; i < handoffs.length; i++) {
      if (data && data.intent === handoffs[i][0] && data[handoffs[i][1]]) {
        window.location.assign(data[handoffs[i][1]]);
        return;
      }
    }

    if (!data || !data.response) throw new Error('The Guide returned no response.');
    assertVisitorLanguageBoundary(data);

    var responseText = document.getElementById('archive-response-text');
    if (!responseText) throw new Error('The response surface is unavailable.');
    responseText.innerHTML = (typeof marked !== 'undefined')
      ? marked.parse(data.response)
      : escapeHtml(data.response).replace(/\n/g, '<br>');

    guideConversationHistory.push({ role: 'assistant', content: data.response });
    renderAuthoritativeRecommendation(data);
    renderOrdinaryFollowupPanel(data.response);

    var responseBox = document.getElementById('archive-response-box');
    if (responseBox) responseBox.style.display = 'block';
    input.value = '';
    var nextInput = document.getElementById('archive-ordinary-followup-input');
    if (nextInput) nextInput.focus();
    console.info('The Guide ordinary conversation continued.', {
      build: USE_FRONTEND_BUILD,
      turns: guideConversationHistory.length
    });
  } catch (error) {
    guideConversationHistory.pop();
    status.textContent = 'Your reply could not be sent just now. Please try again.';
    console.error('The Guide ordinary follow-up failed.', error);
  } finally {
    guideOrdinaryFollowupInFlight = false;
    if (button.isConnected) {
      button.disabled = false;
      button.textContent = 'Reply';
    }
  }
}

/* ================================================================
   MAIN GUIDE SUBMISSION
   ================================================================ */

async function useGuideSubmit(event) {

  event.preventDefault();

  var inputEl =
    document.getElementById(
      'archive-query-input'
    );

  var responseBox =
    document.getElementById(
      'archive-response-box'
    );

  var responseText =
    document.getElementById(
      'archive-response-text'
    );

  var responseControls =
    document.getElementById(
      'archive-response-controls'
    );

  var submitBtn =
    document.getElementById(
      'archive-submit-btn'
    );

  var submitLabel =
    submitBtn
      ? submitBtn.querySelector(
          '.archive-button-label'
        )
      : null;

  if (!inputEl || !submitBtn) {
    return;
  }

  var query =
    inputEl.value.trim();

  if (!query) {
    return;
  }

  var requestToken = ++guideRequestSequence;
  guideActiveRequestToken = requestToken;

  if (guideSafetyActive) {

    var safetyInput =
      document.getElementById(
        'archive-safety-input'
      );

    if (safetyInput) {
      safetyInput.focus();
    }

    return;
  }

  resetGuideConversationHistory();
  guideLastRecommendation = null;

  guideConversationHistory.push({
    role: 'visitor',
    content: query
  });

  /*
   * Immediate visitor feedback while USE
   * determines the authoritative route.
   */

  submitBtn.disabled = true;

  submitBtn.classList.add(
    'is-loading'
  );

  submitBtn.setAttribute(
    'aria-busy',
    'true'
  );

  submitBtn.setAttribute(
    'aria-label',
    'Searching…'
  );

  if (submitLabel) {
    submitLabel.textContent = 'Searching…';
  }

  /*
   * Give the browser one paint opportunity before the network request.
   * This makes the loading state visible even when USE returns or redirects
   * very quickly, rather than leaving the visitor wondering whether the click
   * registered.
   */
  if (
    typeof requestAnimationFrame ===
    'function'
  ) {
    await new Promise(function (resolve) {
      requestAnimationFrame(resolve);
    });
  }

  if (responseControls) {
    responseControls.style.display =
      'none';
  }

  if (responseBox) {
    responseBox.style.display =
      'block';
  }

  if (responseText) {

    responseText.innerHTML =
      '<p><em>Giving this question a little more room...</em></p>';
  }

  try {

    var res =
      await fetchUSE(
        {
          query: query
        },
        'guide-submit'
      );

    if (!res.ok) {

      throw new Error(
        'HTTP status ' +
        res.status
      );
    }

    var data =
      await res.json();

    if (guideActiveRequestToken !== requestToken) return;
    if (data && data.query && String(data.query).trim() !== query) {
      throw new Error('The Guide received a response for a different question.');
    }

    /* ============================================================
       SITEWIDE SAFETY BOUNDARY
       ============================================================ */

    if (
      hasAuthoritativeSafetyPayload(
        data
      )
    ) {

      guideConversationHistory.push({
        role: 'assistant',
        content:
          data.safety_message ||
          data.response ||
          '',
        question:
          data.safety_question ||
          ''
      });

      renderSafetyResponse(
        data
      );

      return;
    }

    /* ============================================================
       HRN SPECIALIST HANDOFF
       ============================================================ */

    if (
      data &&
      data.intent ===
        'RELATIONAL_HANDOFF' &&
      data.relational_delegation
    ) {

      var delegation =
        data.relational_delegation;

      var seed =
        delegation.seed_message ||
        query;

      var session =
        delegation.session_id ||
        '';

      var destination =
        HRN_PAGE_URL +
        '?hrn_seed=' +
        encodeURIComponent(seed) +
        '&hrn_session=' +
        encodeURIComponent(session);

      console.info(
        'The Guide HRN handoff: contract=' +
        USE_HRN_HANDOFF_CONTRACT +
        ', session=' + session
      );

      window.location.assign(
        destination
      );

      return;
    }

    /* ============================================================
       GLOSSARY HANDOFF
       ============================================================ */

    if (
      data &&
      data.intent ===
        'GLOSSARY_HANDOFF' &&
      data.glossary_url
    ) {

      window.location.assign(
        data.glossary_url
      );

      return;
    }

    /* ============================================================
       CATALOGUE HANDOFF
       ============================================================ */

    if (
      data &&
      data.intent ===
        'CATALOGUE_HANDOFF' &&
      data.catalogue_url
    ) {

      window.location.assign(
        data.catalogue_url
      );

      return;
    }

    /* ============================================================
       ATLAS HANDOFF
       ============================================================ */

    if (
      data &&
      data.intent ===
        'ATLAS_HANDOFF' &&
      data.atlas_url
    ) {

      window.location.assign(
        data.atlas_url
      );

      return;
    }

    /* ============================================================
       GUIDE NODE HANDOFF
       ============================================================ */

    if (
      data &&
      data.intent ===
        'GUIDE_NODE_HANDOFF' &&
      data.guide_node_url
    ) {

      window.location.assign(
        data.guide_node_url
      );

      return;
    }

    /* ============================================================
       NAVIGATOR HANDOFF
       ============================================================ */

    if (
      data &&
      data.intent ===
        'NAVIGATOR_HANDOFF' &&
      data.navigator_url
    ) {

      window.location.assign(
        data.navigator_url
      );

      return;
    }

    /* ============================================================
       GLYPH HANDOFF
       ============================================================ */

    if (
      data &&
      data.intent ===
        'GLYPH_HANDOFF' &&
      data.glyph_url
    ) {

      window.location.assign(
        data.glyph_url
      );

      return;
    }

    /* ============================================================
       PHILIPPINE SYSTEMS HANDOFF
       ============================================================ */

    if (
      data &&
      data.intent ===
        'SYSTEMS_PH_HANDOFF' &&
      data.philippine_systems_url
    ) {

      window.location.assign(
        data.philippine_systems_url
      );

      return;
    }

    /* ============================================================
       FSD HANDOFF
       ============================================================ */

    if (
      data &&
      data.intent ===
        'FSD_HANDOFF' &&
      data.fsd_url
    ) {

      window.location.assign(
        data.fsd_url
      );

      return;
    }

    /* ============================================================
       CASE NAVIGATOR HANDOFF
       ============================================================ */

    if (
      data &&
      data.intent ===
        'CASE_HANDOFF' &&
      data.case_url
    ) {

      window.location.assign(
        data.case_url
      );

      return;
    }

    /* ============================================================
       FINAL SAFETY FAIL-CLOSED BOUNDARY
       ============================================================ */

    if (
      hasAuthoritativeSafetyPayload(
        data
      )
    ) {

      throw new Error(
        'Safety payload reached ordinary response boundary'
      );
    }

    /* ============================================================
       ORDINARY USE RESPONSE
       ============================================================ */

    if (
      data &&
      data.response
    ) {

      /*
       * Final browser-side defense in depth. Do not sanitize/rewrite here:
       * the backend owns the visitor voice. If internal metadata survives
       * the backend boundary, refuse to render it rather than exposing it.
       */
      assertVisitorLanguageBoundary(data);

      /*
       * Render the substantive answer first. Markdown and optional UI
       * components are non-authoritative presentation layers: a defect in
       * any of them must never erase a valid backend answer or be mislabeled
       * as a service connection failure.
       */
      var renderedAnswer = '';
      try {
        if (typeof marked !== 'undefined' && marked && typeof marked.parse === 'function') {
          renderedAnswer = marked.parse(data.response);
        } else {
          renderedAnswer = escapeHtml(data.response).replace(/\r?\n/g, '<br>');
        }
      } catch (markdownError) {
        console.error('The Guide Markdown renderer failed; using safe plain text.', markdownError);
        renderedAnswer = escapeHtml(data.response).replace(/\r?\n/g, '<br>');
      }
      renderGuidePayload(responseText, data.response, query, requestToken);

      guideConversationHistory.push({
        role: 'assistant',
        content: data.response
      });

      try {
        renderAuthoritativeRecommendation(data);
      } catch (recommendationError) {
        console.error('The Guide answer rendered, but its optional recommendation UI failed.', recommendationError);
      }

      try {
        renderOrdinaryFollowupPanel(data.response);
      } catch (followupError) {
        console.error('The Guide answer rendered, but its optional follow-up UI failed.', followupError);
      }

      try {
        configureResponseControl(data.response);
        if (responseControls) responseControls.style.display = 'flex';
      } catch (controlError) {
        console.error('The Guide answer rendered, but its optional response controls failed.', controlError);
      }

    } else {

      responseText.innerHTML =
        '<p>No matching pathways found.</p>';
    }

  } catch (error) {

    console.error('The Guide request failed before a complete answer could be rendered.', error);

    if (responseText) {
      responseText.innerHTML =
        "<p style='color: #b91c1c;'>" +
        "The Guide could not complete this request. Please try again." +
        "</p>";
    }

  } finally {

    submitBtn.disabled = false;

    submitBtn.classList.remove(
      'is-loading'
    );

    submitBtn.removeAttribute(
      'aria-busy'
    );

    submitBtn.setAttribute(
      'aria-label',
      'Search'
    );

    if (submitLabel) {
      submitLabel.textContent = 'Search';
    }  }
}

/* ================================================================
   SINGLE SUBMISSION OWNER
   Exactly one document-level capture listener owns Guide submissions.
   No form-level listener is installed alongside it.
   ================================================================ */

function installGuideSubmitController() {
  /*
   * Bind to this exact instance, not the document. The click owner also
   * bypasses submit-event interference from duplicate-ID forms/plugins.
   */
  var form = guideRoot.querySelector('#archive-search-form');
  var button = guideRoot.querySelector('#archive-submit-btn');

  if (!form || !button) {
    console.error('The Guide Woody controller could not find its form or Search button.');
    return;
  }

  if (form.dataset.useGuideControllerInstalled === USE_FRONTEND_BUILD) return;

  form.removeAttribute('onsubmit');
  form.setAttribute('data-use-frontend-build', USE_FRONTEND_BUILD);
  form.dataset.useGuideControllerInstalled = USE_FRONTEND_BUILD;

  var submitInFlight = false;
  function submitFromWoody(event) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
      if (typeof event.stopImmediatePropagation === 'function') event.stopImmediatePropagation();
    }
    if (submitInFlight) return;
    submitInFlight = true;
    Promise.resolve(useGuideSubmit({
      preventDefault: function () {}
    })).finally(function () {
      submitInFlight = false;
    });
  }

  button.addEventListener('click', function (event) {
    submitFromWoody(event);
  }, true);

  form.addEventListener('submit', function (event) {
    submitFromWoody(event);
  }, true);

  guideRoot.__USE_GUIDE_DELEGATED_SUBMIT_CONTROLLER__ = USE_FRONTEND_BUILD;
  guideRoot.__USE_GUIDE_FRONTEND_CONTROLLER__ = {
    build: USE_FRONTEND_BUILD,
    authority: USE_FRONTEND_AUTHORITY,
    endpoint: USE_API_ENDPOINT
  };
}

function initializeGuideFrontend() {

  initializeGuideQueryField();

  installGuideSubmitController();

  initializeGuideHints();


  installSafetyFollowupController();
}

if (
  document.readyState ===
  'loading'
) {

  document.addEventListener(
    'DOMContentLoaded',
    initializeGuideFrontend
  );

} else {

  initializeGuideFrontend();
}

/* ================================================================
   RESET
   ================================================================ */

function resetArchiveSearch() {

  var input =
    document.getElementById(
      'archive-query-input'
    );

  var safetyInput =
    document.getElementById(
      'archive-safety-input'
    );

  var safetyFollowup =
    document.getElementById(
      'archive-safety-followup'
    );

  var submitBtn =
    document.getElementById(
      'archive-submit-btn'
    );

  resetGuideConversationHistory();

  if (input) {

    input.value = '';

    input.disabled = false;
  }

  if (submitBtn) {

    submitBtn.disabled = false;

    submitBtn.classList.remove(
      'is-loading'
    );
  }

  if (safetyInput) {

    safetyInput.value = '';

    safetyInput.disabled = false;
  }

  if (safetyFollowup) {

    safetyFollowup.style.display =
      'none';
  }

  var safetyResources =
    document.getElementById(
      'archive-safety-resources'
    );

  if (safetyResources) {

    safetyResources.innerHTML =
      '';

    safetyResources.style.display =
      'none';
  }

  var safetyContainer =
    document.getElementById(
      'archive-container-top'
    );

  if (safetyContainer) {

    safetyContainer.classList.remove(
      'archive-safety-active'
    );
  }

  guideHintIndex = 0;

  startGuideHintRotation();

  var responseBox =
    document.getElementById(
      'archive-response-box'
    );

  if (responseBox) {

    responseBox.style.display =
      'none';
  }

  var responseControls =
    document.getElementById(
      'archive-response-controls'
    );

  if (responseControls) {

    responseControls.style.display =
      'none';
  }

  var controlButton =
    document.querySelector(
      '#archive-response-controls .reset-btn'
    );

  if (controlButton) {

    controlButton.classList.remove(
      'continue-inquiry'
    );

    controlButton.setAttribute(
      'data-response-mode',
      'reset'
    );
  }

  var controlIcon =
    document.getElementById(
      'archive-response-control-icon'
    );

  var controlLabel =
    document.getElementById(
      'archive-response-control-label'
    );

  if (controlIcon) {
    controlIcon.textContent = '↺';
  }

  if (controlLabel) {

    controlLabel.textContent =
      'Start another question';
  }

  var responseText =
    document.getElementById(
      'archive-response-text'
    );

  if (responseText) {

    responseText.innerHTML =
      '';
  }

  var recommendation =
    document.getElementById(
      'archive-recommendation'
    );

  if (recommendation) {

    recommendation.innerHTML =
      '';

    recommendation.style.display =
      'none';
  }
}

  var resetButton = guideRoot.querySelector('.reset-btn');
  if (resetButton) {
    resetButton.removeAttribute('onclick');
    resetButton.addEventListener('click', function (event) {
      event.preventDefault();
      handleResponseControl();
    });
  }

    return true;
  }

  function startGuideWoodyController() {
    if (bootGuideWoodyController()) return;
    if (!nativeDocument.documentElement) return;
    var observer = new MutationObserver(function () {
      if (bootGuideWoodyController()) observer.disconnect();
    });
    observer.observe(nativeDocument.documentElement, { childList: true, subtree: true });
  }

  if (nativeDocument.readyState === 'loading') {
    nativeDocument.addEventListener('DOMContentLoaded', startGuideWoodyController, { once: true });
  } else {
    startGuideWoodyController();
  }
})(window, window.document);
