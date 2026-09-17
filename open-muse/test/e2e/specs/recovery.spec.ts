import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
const controlOrigin = `http://127.0.0.1:${process.env.OPEN_MUSE_E2E_CONTROL_PORT ?? 4319}`;

type HarnessState = {
  managerGeneration: number;
  agentCreations: number;
  computerCreations: number;
  dispatchCount: number;
  terminalCount: number;
  observationCount: number;
  conversation?: { id: string; messages: unknown[]; pendingApproval?: { approvalId: string }; recovery?: unknown };
};

async function setScenario(request: APIRequestContext, scenario: "failed_before_execution" | "outcome_unknown"): Promise<void> {
  const response = await request.post(`${controlOrigin}/__e2e/scenario`, { data: { scenario } });
  expect(response.ok()).toBeTruthy();
}

async function requestAndApprove(page: Page): Promise<void> {
  await page.goto("/");
  await page.getByRole("button", { name: /Try a public web task/ }).click();
  await expect(page.getByText("Approval required")).toBeVisible();
  await page.getByRole("button", { name: "Approve once" }).click();
}

async function harnessState(request: APIRequestContext): Promise<HarnessState> {
  return await (await request.get(`${controlOrigin}/__e2e/state`)).json() as HarnessState;
}

test.beforeEach(async ({ request }) => {
  await request.post(`${controlOrigin}/__e2e/reset`);
});

test("safe pre-dispatch failure survives reload and Continue requires fresh approval", async ({ page, request }) => {
  await setScenario(request, "failed_before_execution");
  await requestAndApprove(page);

  await expect(page.getByText("Action did not run", { exact: true })).toBeVisible();
  await expect(page.getByText(/Run approved browser operation did not run/)).toBeVisible();
  const beforeRestart = await harnessState(request);
  await request.post(`${controlOrigin}/__e2e/restart`);
  await page.reload();
  await expect(page.getByText("Action did not run", { exact: true })).toBeVisible();
  expect((await harnessState(request)).managerGeneration).toBe(beforeRestart.managerGeneration + 1);

  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByText("Approval required")).toBeVisible();
  await expect(page.getByText("Click button “Open result”", { exact: true })).toBeVisible();
  const state = await harnessState(request);
  expect(state.dispatchCount).toBe(0);
  expect(state.terminalCount).toBe(1);
  expect(state.conversation?.pendingApproval?.approvalId).toBeTruthy();
  expect(state.agentCreations).toBeGreaterThanOrEqual(2);
  expect(state.computerCreations).toBeGreaterThanOrEqual(2);
});

test("unknown outcome survives reload and Continue observes without replay", async ({ page, request }) => {
  await setScenario(request, "outcome_unknown");
  await requestAndApprove(page);

  await expect(page.getByText("Action outcome unknown", { exact: true })).toBeVisible();
  await expect(page.getByText(/Run approved browser operation may have completed/)).toBeVisible();
  const beforeRestart = await harnessState(request);
  await request.post(`${controlOrigin}/__e2e/restart`);
  await page.reload();
  await expect(page.getByText("Check before doing it again")).toBeVisible();
  expect((await harnessState(request)).managerGeneration).toBe(beforeRestart.managerGeneration + 1);

  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByText("I inspected the current page before deciding what to do next.")).toBeVisible();
  await expect(page.getByText("Approval required")).toBeHidden();
  const state = await harnessState(request);
  expect(state.dispatchCount).toBe(1);
  expect(state.terminalCount).toBe(1);
  expect(state.observationCount).toBe(2);
  expect(state.conversation?.pendingApproval).toBeUndefined();
});

test("Start over replaces unknown work with a clean conversation", async ({ page, request }) => {
  await setScenario(request, "outcome_unknown");
  await requestAndApprove(page);
  await expect(page.getByText("Action outcome unknown", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Start over" }).click();

  await expect(page.getByRole("heading", { name: /What should we get done/ })).toBeVisible();
  const state = await harnessState(request);
  expect(state.conversation?.id).toBeTruthy();
  expect(state.conversation?.messages).toEqual([]);
  expect(state.conversation?.recovery).toBeUndefined();
});

test("Start over blocks overlapping conversation changes while reset is pending", async ({ page, request }) => {
  await setScenario(request, "outcome_unknown");
  await requestAndApprove(page);
  await expect(page.getByText("Action outcome unknown", { exact: true })).toBeVisible();

  let releaseReset!: () => void;
  const resetBlocked = new Promise<void>((resolve) => { releaseReset = resolve; });
  let markResetStarted!: () => void;
  const resetStarted = new Promise<void>((resolve) => { markResetStarted = resolve; });
  await page.route("**/api/conversations/*/commands", async (route) => {
    const body = route.request().postDataJSON() as { command?: { kind?: string } };
    if (body.command?.kind !== "start_over") return route.continue();
    markResetStarted();
    await resetBlocked;
    await route.continue();
  });

  await page.getByRole("button", { name: "Start over" }).click();
  await resetStarted;
  await expect(page.locator("header").getByText("Changing conversation…", { exact: true })).toBeVisible();
  await page.getByText("Chats", { exact: true }).click();
  await expect(page.getByRole("button", { name: /New chat/ })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Reset conversation" })).toBeDisabled();

  releaseReset();
  await expect(page.getByRole("heading", { name: /What should we get done/ })).toBeVisible();
});

test("concurrent duplicate approval submissions produce one terminal result", async ({ page, request }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Try a public web task/ }).click();
  await expect(page.getByText("Approval required")).toBeVisible();

  const responses = await page.evaluate(async () => {
    const conversation = await fetch("/api/bootstrap").then((response) => response.json()) as { conversationId: string; csrfToken: string };
    const snapshot = await fetch(`/api/conversations/${conversation.conversationId}`).then((response) => response.json()) as { pendingApproval: { approvalId: string; actionDigest: string } };
    const path = `/api/conversations/${conversation.conversationId}/commands`;
    const options = {
      method: "POST",
      headers: { "content-type": "application/json", "x-smol-csrf": conversation.csrfToken },
      body: JSON.stringify({ commandId: "approve-duplicate", command: { kind: "approve", approvalId: snapshot.pendingApproval.approvalId, actionDigest: snapshot.pendingApproval.actionDigest } }),
    };
    return await Promise.all([fetch(path, options).then((response) => response.status), fetch(path, options).then((response) => response.status)]);
  });

  expect(responses).toEqual([200, 200]);
  await expect(page.getByText("The scripted browser opened Example Domain.")).toBeVisible();
  const state = await harnessState(request);
  expect(state.dispatchCount).toBe(1);
  expect(state.terminalCount).toBe(1);
  expect(state.conversation?.messages).toHaveLength(2);
});
