import { expect, test } from "@playwright/test";
const controlOrigin = `http://127.0.0.1:${process.env.OPEN_MUSE_E2E_CONTROL_PORT ?? 4319}`;

test.beforeEach(async ({ request }) => {
  await request.post(`${controlOrigin}/__e2e/reset`);
});

test("approves a scripted browser operation through the original suspended turn", async ({ page, request }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /What should we get done/ })).toBeVisible();

  await page.getByRole("button", { name: /Try a public web task/ }).click();

  await expect(page.getByText("Approval required")).toBeVisible();
  await expect(page.getByText("Click button “Open result”", { exact: true })).toBeVisible();
  await expect(page.getByText("Current page: https://example.com/", { exact: true })).toBeVisible();
  const beforeApproval = await (await request.get(`${controlOrigin}/__e2e/state`)).json() as { conversation?: { messages: unknown[] } };
  expect(beforeApproval.conversation?.messages).toHaveLength(1);
  await page.getByRole("button", { name: "Approve once" }).click();

  await expect(page.getByText("The scripted browser opened Example Domain.")).toBeVisible();
  await expect(page.getByText("Approval required")).toBeHidden();
});

test("public navigation completes without confirmation", async ({ page }) => {
  await page.goto("/");
  await page.getByPlaceholder("Message OpenMuse…").fill("Navigate only");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.getByText("Navigation completed without confirmation.")).toBeVisible();
  await expect(page.getByText("Approval required")).toBeHidden();
});

test("declines a scripted browser operation without executing it", async ({ page, request }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Try a public web task/ }).click();
  await expect(page.getByText("Approval required")).toBeVisible();

  await page.getByRole("button", { name: "Not now" }).click();

  await expect(page.getByText("Approval required")).toBeHidden();
  const state = await request.get(`${controlOrigin}/__e2e/state`);
  expect(state.ok()).toBeTruthy();
  expect(await state.json()).toMatchObject({ dispatchCount: 0, terminalCount: 0 });
});
