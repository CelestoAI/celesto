import { test, expect } from "@playwright/test";
import { executeBrowserOperation } from "../../../server/browser-driver.js";

test("Enter returns evidence from delayed search results without replay", async ({ page }, testInfo) => {
  await page.route("https://search-fixture.example/**", (route) => route.fulfill({
    contentType: "text/html; charset=utf-8",
    body: `<form><input aria-label="Search products"><button>Search</button></form>
      <main></main><script>
      window.submissions = 0;
      document.querySelector('form').onsubmit = event => {
        event.preventDefault(); window.submissions++;
        setTimeout(() => document.querySelector('main').textContent = 'Fixture phone 256 GB — ₹1,64,900', 200);
      };
      </script>`,
  }));
  await page.goto("https://search-fixture.example/");
  await page.getByRole("textbox").fill("Fixture phone");
  const result = await executeBrowserOperation(page, { kind: "keypress", key: "Enter" }) as { observation?: { snapshot: string } };
  expect(result.observation?.snapshot).toContain("₹1,64,900");
  expect(await page.evaluate(() => (window as unknown as { submissions: number }).submissions)).toBe(1);
  await testInfo.attach("post-submit-evidence", { body: JSON.stringify(result), contentType: "application/json" });
  await testInfo.attach("post-submit-page", { body: await page.screenshot(), contentType: "image/png" });
});

// Catch server-only variables accidentally referenced inside browser callbacks.
// Also verify that passing the pattern retains credential-field protection.
test("search evaluates its safety pattern inside Chromium", async ({ page }, testInfo) => {
  await page.route("https://search-fixture.example/**", async (route) => {
    const url = new URL(route.request().url());
    await route.fulfill({
      contentType: "text/html",
      body: url.pathname === "/search"
        ? "<h1>Search results</h1>"
        : '<form action="/search" method="get"><input aria-label="Search products" name="q" data-celesto-browser-ref="00000000-0000-4000-8000-000000000001"></form>',
    });
  });
  await page.goto("https://search-fixture.example/");
  const operation = {
    kind: "search" as const, ref: "e1", query: "phone",
    target: { role: "textbox", name: "Search products", nth: 0, locatorId: "00000000-0000-4000-8000-000000000001" },
  };
  await executeBrowserOperation(page, operation);
  await expect(page).toHaveURL("https://search-fixture.example/search?q=phone");
  await expect(page.getByRole("heading")).toHaveText("Search results");
  await testInfo.attach("search-results", { body: await page.screenshot(), contentType: "image/png" });

  await page.goto("https://search-fixture.example/");
  await page.getByRole("textbox").evaluate((input) => input.setAttribute("autocomplete", "username"));
  await expect(executeBrowserOperation(page, operation)).rejects.toMatchObject({ code: "SEARCH_FORM_UNSUPPORTED" });
  await expect(page).toHaveURL("https://search-fixture.example/");
  await testInfo.attach("credential-field-blocked", {
    body: JSON.stringify({ code: "SEARCH_FORM_UNSUPPORTED", navigationPrevented: true }),
    contentType: "application/json",
  });
});
