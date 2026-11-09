// Frontend safety candidate contract.
// This file is the repository copy of the isolated WordPress candidate artifact.
// Production Guide asset references must not be changed by this branch.
(function () {
  'use strict';
  function inferSafetyCountryCandidate() {
    try {
      var locale = (navigator.languages && navigator.languages[0]) || navigator.language || '';
      var match = String(locale).match(/[-_]([A-Z]{2})$/i);
      var code = match ? match[1].toUpperCase() : '';
      if (code && typeof Intl !== 'undefined' && Intl.DisplayNames) {
        return new Intl.DisplayNames([navigator.language || 'en'], { type: 'region' }).of(code) || '';
      }
    } catch (ignore) {}
    return '';
  }

  window.__livingArchiveSafetyCandidateContract = {
    inferSafetyCountryCandidate: inferSafetyCountryCandidate,
    openingLocationParagraphRemoved: true,
    confirmationText: 'It looks like you may be in [country]. Is that correct?',
    yesBehavior: 'accept inferred country',
    noBehavior: 'reveal manual country fallback'
  };
}());
