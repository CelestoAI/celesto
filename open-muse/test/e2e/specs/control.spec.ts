import { expect, test } from "@playwright/test";
const controlOrigin = `http://127.0.0.1:${process.env.OPEN_MUSE_E2E_CONTROL_PORT ?? 4319}`;

test.beforeEach(async ({ request }) => {
  await request.post(`${controlOrigin}/__e2e/reset`);
});

test("uses the real UI to take control, return control, and stop", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /What should we get done/ })).toBeVisible();
  await page.getByRole("button", { name: /Try a public web task/ }).click();
  await expect(page.getByText("Approval required")).toBeVisible();
  await page.getByRole("button", { name: "Not now" }).click();
  await expect(page.getByTitle("Live OpenMuse computer")).toBeVisible();

  await page.locator(".computer-actions").getByRole("button", { name: "Take control" }).click();
  await expect(page.locator("header").getByText("You have control", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Return control" })).toBeVisible();

  await page.getByRole("button", { name: "Return control" }).click();
  await expect(page.getByText("Ready", { exact: true })).toBeVisible();

  await page.locator(".top-actions").getByRole("button", { name: "Stop" }).click();
  await expect(page.getByText("Stopped", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Computer deleted" })).toBeVisible();
  await page.getByText("Chats", { exact: true }).click();
  await page.getByRole("button", { name: "+ New chat", exact: true }).click();
  await expect(page.getByText("Ready", { exact: true })).toBeVisible();
  await expect(page.getByPlaceholder("Message OpenMuse…")).toBeEnabled();
  await expect(page.getByRole("heading", { name: "Computer deleted" })).not.toBeVisible();
});

test("waits for the takeover token before enabling Return control", async ({ page }) => {
  let releaseTakeover!: () => void;
  const takeoverHeld = new Promise<void>((resolve) => { releaseTakeover = resolve; });
  await page.route("**/api/conversations/*/commands", async (route) => {
    if (route.request().postDataJSON().command.kind !== "take_control") {
      await route.continue();
      return;
    }
    const response = await route.fetch();
    await takeoverHeld;
    await route.fulfill({ response });
  });

  try {
    await page.goto("/");
    await page.getByRole("button", { name: /Try a public web task/ }).click();
    await expect(page.getByText("Approval required")).toBeVisible();
    await page.getByRole("button", { name: "Not now" }).click();
    await expect(page.getByText("Ready", { exact: true })).toBeVisible();
    await expect(page.getByTitle("Live OpenMuse computer")).toBeVisible();
    await page.locator(".computer-actions").getByRole("button", { name: "Take control" }).click();

    // The event stream announces human control while the HTTP token response is held.
    await expect(page.locator("header").getByText("You have control", { exact: true })).toBeVisible();
    const returnControl = page.getByRole("button", { name: "Return control" });
    await expect(returnControl).toBeDisabled();
    releaseTakeover();
    await expect(returnControl).toBeEnabled();
    const returned = page.waitForResponse((response) =>
      response.url().endsWith("/commands") &&
      response.request().postDataJSON().command.kind === "return_control");
    await returnControl.click();
    expect((await returned).status()).toBe(200);
    await expect(page.getByText("Ready", { exact: true })).toBeVisible();
  } finally {
    releaseTakeover();
  }
});
