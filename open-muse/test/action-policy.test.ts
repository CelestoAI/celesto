import assert from "node:assert/strict";
import test from "node:test";
import { decideBrowserAction } from "../server/action-policy.js";
import type { BrowserTarget, ExecutableBrowserOperation } from "../server/browser-operations.js";

const target = (role: string, name: string): BrowserTarget => ({
  role, name, publicName: name, nth: 0, locatorId: "00000000-0000-4000-8000-000000000001",
});

test("research actions flow without confirmation", () => {
  const operations: ExecutableBrowserOperation[] = [
    { kind: "observe" },
    { kind: "extract" },
    { kind: "scroll", direction: "down" },
    { kind: "navigate", url: "https://example.com/" },
    { kind: "follow_link", ref: "e1", target: target("link", "Learn more") },
    { kind: "search", ref: "e2", query: "OpenMuse", target: target("searchbox", "Search") },
  ];

  for (const operation of operations) assert.equal(decideBrowserAction(operation).decision, "allow", operation.kind);
});

test("effectful actions confirm and secret entry is denied", () => {
  assert.equal(decideBrowserAction({ kind: "click", ref: "e1", target: target("button", "Subscribe") }).decision, "confirm");
  assert.equal(decideBrowserAction({ kind: "fill", ref: "e2", value: "Aniket", target: target("textbox", "Name") }).decision, "confirm");
  assert.equal(decideBrowserAction({ kind: "select", ref: "e3", label: "India", target: target("combobox", "Country") }).decision, "confirm");
  assert.equal(decideBrowserAction({ kind: "keypress", key: "Enter" }).decision, "confirm");
  assert.equal(decideBrowserAction({ kind: "fill", ref: "e4", value: "secret", target: target("textbox", "Password") }).decision, "deny");
});
