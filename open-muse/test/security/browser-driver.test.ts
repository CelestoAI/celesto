import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import test from "node:test";
import { chromium } from "playwright-core";
import { executeBrowserOperation } from "../../server/browser-driver.js";

test("real browser observations redact populated fields and reject private destinations", async () => {
  const browser = await chromium.launch({
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    headless: true,
  });
  const evidence: Record<string, unknown> = {};
  try {
    const context = await browser.newContext();
    await context.route("https://example.com/**", (route) => route.fulfill({
      contentType: "text/html",
      body: '<title>Profile</title><label>Email<input value="ada@example.com"></label><label>Card<input value="4111 1111 1111 1111"></label><button>Contact ada@example.com</button><p>Write to ada@example.com</p>',
    }));
    const page = await context.newPage();
    await page.goto("https://example.com/");
    const result = await executeBrowserOperation(page, { kind: "observe" }) as { snapshot: string };
    evidence.snapshot = result.snapshot;
    assert.doesNotMatch(result.snapshot, /ada@example\.com|4111/);
    assert.match(result.snapshot, /\[email redacted\]/);
    assert.match(result.snapshot, /\[number redacted\]/);
    await context.route("http://127.0.0.1/**", (route) => route.fulfill({ body: "PRIVATE-DATA" }));
    await page.goto("http://127.0.0.1/");
    for (const kind of ["observe", "extract"] as const) {
      await assert.rejects(executeBrowserOperation(page, { kind }), /private or local/);
    }
    evidence.privateObservationRejected = true;
  } finally {
    await mkdir("../artifacts/security-scan", { recursive: true });
    await writeFile("../artifacts/security-scan/browser-driver.json", JSON.stringify(evidence, null, 2));
    await browser.close();
  }
});
