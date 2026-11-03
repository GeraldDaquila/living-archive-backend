"use strict";
const assert = require("node:assert/strict");
const transport = require("./guide_active_active_transport.js");

const primary = "https://primary.example/api/query";
const secondary = "https://secondary.example/api/query";

assert.equal(transport.secondaryWeight, 0.20);
assert.deepEqual(transport.endpointOrder(primary, secondary, 0), [
  { name: "secondary", endpoint: secondary },
  { name: "primary", endpoint: primary }
]);
assert.deepEqual(transport.endpointOrder(primary, secondary, 0.199999), [
  { name: "secondary", endpoint: secondary },
  { name: "primary", endpoint: primary }
]);
assert.deepEqual(transport.endpointOrder(primary, secondary, 0.20), [
  { name: "primary", endpoint: primary },
  { name: "secondary", endpoint: secondary }
]);
assert.deepEqual(transport.endpointOrder(primary, secondary, 0.999), [
  { name: "primary", endpoint: primary },
  { name: "secondary", endpoint: secondary }
]);
assert.deepEqual(transport.endpointOrder("", secondary, 0.9), [
  { name: "secondary", endpoint: secondary }
]);
assert.deepEqual(transport.endpointOrder(primary, "", 0.1), [
  { name: "primary", endpoint: primary }
]);
assert.deepEqual(transport.endpointOrder("", "", 0.5), []);
assert.deepEqual(transport.endpointOrder(primary, secondary, NaN).sort((a,b) => a.name.localeCompare(b.name)), [
  { name: "primary", endpoint: primary },
  { name: "secondary", endpoint: secondary }
].sort((a,b) => a.name.localeCompare(b.name)));

console.log("Guide active-active transport contract: 8 assertions passed");
