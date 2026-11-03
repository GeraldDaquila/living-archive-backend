/* Guide transport endpoint selection — active-active canary contract.
 * This distributes distinct visitor requests across the existing primary and
 * mirror services. It does not duplicate a visitor request or infer quota
 * independence from separate server processes.
 */
(function (root) {
  "use strict";

  var SECONDARY_WEIGHT = 0.20;

  function endpointOrder(primary, secondary, sample) {
    var first = String(primary || "").trim();
    var second = String(secondary || "").trim();
    if (!first && !second) return [];
    if (!first) return [{ name: "secondary", endpoint: second }];
    if (!second) return [{ name: "primary", endpoint: first }];

    var roll = Number(sample);
    if (!Number.isFinite(roll)) roll = Math.random();
    roll = Math.max(0, Math.min(0.999999999, roll));

    var primaryAttempt = { name: "primary", endpoint: first };
    var secondaryAttempt = { name: "secondary", endpoint: second };
    return roll < SECONDARY_WEIGHT
      ? [secondaryAttempt, primaryAttempt]
      : [primaryAttempt, secondaryAttempt];
  }

  var api = Object.freeze({
    secondaryWeight: SECONDARY_WEIGHT,
    endpointOrder: endpointOrder
  });

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.LAGuideActiveActiveTransport = api;
  }
})(typeof window !== "undefined" ? window : null);
