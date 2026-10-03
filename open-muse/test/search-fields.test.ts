import assert from "node:assert/strict";
import test from "node:test";
import { isSearchFieldCandidate } from "../server/search-fields.js";
import { decideBrowserAction } from "../server/action-policy.js";

// Failure cases: sensitive labels accepted by either role, legitimate search
// rejected, or search-only exclusions accidentally changing fill policy.
test("public search rejects sensitive labels for both input roles", () => {
  for (const role of ["textbox", "searchbox"]) {
    for (const label of [
      "token", "secret", "credential", "password", "passcode", "otp",
      "credit card", "payment", "cvv", "cvc", "security code",
      "verification code", "expiry", "email", "phone", "verification",
    ]) {
      assert.equal(isSearchFieldCandidate({ role, name: `Search ${label}` }), false, `${role}: Search ${label}`);
    }
  }
});

test("ordinary search fields remain supported", () => {
  assert.equal(isSearchFieldCandidate({ role: "textbox", name: "Search for Products, Brands and More" }), true);
  assert.equal(isSearchFieldCandidate({ role: "searchbox", name: "Find products" }), true);
  assert.equal(isSearchFieldCandidate({ role: "textbox", name: "Your name" }), false);
  assert.equal(isSearchFieldCandidate({ role: "button", name: "Search" }), false);
});

test("search-only exclusions do not change fill policy", () => {
  for (const name of ["Email", "Phone", "Verification"]) {
    const decision = decideBrowserAction({
      kind: "fill", ref: "e1",
      target: { role: "textbox", name, nth: 0 }, value: "example",
    });
    assert.equal(decision.decision, "confirm", name);
  }
});
