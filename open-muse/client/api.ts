import type { TraceTurn } from "./trace";

export interface Message { id: string; role: "user" | "assistant"; text: string; createdAt: string; turnId?: string }
export interface BrowserOperation { kind: string; url?: string; direction?: string; key?: string; value?: string; query?: string; label?: string; target?: { role: string; name: string } }
export interface Approval { kind: "checkout_review" | "browser_program" | "browser_operation"; approvalId: string; actionDigest: string; reason: string; expiresAt: string; totalPriceMinor?: number; operation?: BrowserOperation; pageUrl?: string }
export interface Event { id: number; type: string; createdAt: string; payload: Record<string, unknown> }
export interface Recovery { kind: "failed_before_execution" | "outcome_unknown" | "interrupted" | "computer_unavailable"; operationId?: string; summary?: string }
export interface BrowserTab { id: string; owner: "agent" | "paused" | "human" | "quarantined"; epoch: number; url: string; active: boolean; openerTabId?: string }
export interface Conversation {
  id: string; stateVersion: number; controlOwner: "agent" | "pause_requested" | "human";
  runState: string; sessionLifecycle: string; messages: Message[]; pendingApproval?: Approval;
  activity: { kind: "idle" | "model_running" | "awaiting_confirmation" | "browser_running" | "human_control" | "recovering" | "stopping" | "stopped" | "failed"; approvalId?: string };
  availableCommands: string[];
  turns: TraceTurn[];
  viewerReady: boolean; events: Event[];
  recovery?: Recovery;
  tabs: BrowserTab[];
  providerId: string; modelId: string; modelAccessState: "ready" | "auth_required" | "model_unavailable";
}
export interface ConversationSummary {
  id: string; title: string; providerId: string; modelId: string; runState: string; updatedAt: string;
}
export interface ConversationList { activeConversationId?: string; conversations: ConversationSummary[] }
type ConversationCommand =
  | { kind: "send_message"; text: string }
  | { kind: "approve" | "reject"; approvalId: string; actionDigest: string }
  | { kind: "take_control" }
  | { kind: "return_control"; controlEpoch: string }
  | { kind: "continue" | "start_over" | "stop" }
  | { kind: "reconnect_model" }
  | { kind: "change_model"; providerId: string; modelId: string }
  | { kind: "adopt_popup"; tabId: string };

export interface ModelSelection { providerId: string; modelId: string }
export interface ProviderAccess {
  id: string; name: string; configured: boolean; source?: "account" | "api_key" | "environment";
  environmentVariable?: string;
  methods: Array<{ type: "oauth" | "api_key"; label: string; enabled: boolean; unavailableReason?: string }>;
  models: Array<{ id: string; name: string; recommended: boolean }>;
}
export interface ModelAccess { providers: ProviderAccess[]; selection?: ModelSelection; disconnectingProviderIds: string[] }
export interface AuthPrompt {
  id: string; type: "text" | "secret" | "select" | "manual_code"; message: string; placeholder?: string;
  options?: Array<{ id: string; label: string; description?: string }>;
}
export interface AuthAttempt {
  id: string; providerId: string; state: "starting" | "waiting_for_browser" | "waiting_for_device" | "waiting_for_input" | "succeeded" | "expired" | "cancelled" | "failed";
  createdAt: string; expiresAt: string; prompt?: AuthPrompt; authUrl?: string;
  deviceCode?: { userCode: string; verificationUri: string }; message?: string; error?: string;
}

let csrfToken = "";
export async function bootstrap(): Promise<{ conversationId?: string; modelAccess?: ModelAccess }> {
  const retryDelays = [100, 200, 400, 800, 1_000, 1_000, 1_000];
  let response: Response | undefined;
  for (let attempt = 0; attempt <= retryDelays.length; attempt += 1) {
    try {
      response = await fetch("/api/bootstrap", { credentials: "same-origin" });
      break;
    }
    catch {
      if (attempt === retryDelays.length) {
        throw new Error("The OpenMuse server did not become ready. Check the server log, then reload this page.");
      }
      await new Promise((resolve) => setTimeout(resolve, retryDelays[attempt]));
    }
  }
  if (!response) throw new Error("The OpenMuse server did not become ready. Check the server log, then reload this page.");
  if (!response.ok) throw new Error("Could not start the local OpenMuse session.");
  const result = await response.json() as { csrfToken: string; conversationId?: string; modelAccess?: ModelAccess };
  csrfToken = result.csrfToken;
  return { conversationId: result.conversationId, modelAccess: result.modelAccess };
}
async function request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method, credentials: "same-origin",
    headers: method === "GET" ? undefined : { "content-type": "application/json", "x-smol-csrf": csrfToken },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({})) as T & { error?: string };
  if (!response.ok) throw new Error(data.error ?? "OpenMuse request failed.");
  return data;
}
const command = <T>(id: string, value: ConversationCommand) => request<T>(`/api/conversations/${id}/commands`, "POST", {
  commandId: crypto.randomUUID(),
  command: value,
});
export const listConversations = () => request<ConversationList>("/api/conversations");
export const createConversation = (selection?: ModelSelection) => request<Conversation>("/api/conversations", "POST", selection ?? {});
export const activateConversation = (id: string) => request<Conversation>(`/api/conversations/${id}/activate`, "POST", {});
export const getModelAccess = () => request<ModelAccess>("/api/model-access");
export const selectModel = (selection: ModelSelection) => request<ModelSelection>("/api/model-access/selection", "PUT", selection);
export const startAuth = (providerId: string, method: "oauth" | "api_key") => request<{ attempt: AuthAttempt }>("/api/auth-attempts", "POST", { providerId, method });
export const getAuthAttempt = (attemptId: string) => request<{ attempt: AuthAttempt }>(`/api/auth-attempts/${attemptId}`);
export const submitAuthPrompt = (attemptId: string, promptId: string, value: string) => request<{ attempt: AuthAttempt }>(`/api/auth-attempts/${attemptId}/prompts/${promptId}`, "POST", { value });
export const cancelAuth = (attemptId: string) => request<{ attempt: AuthAttempt }>(`/api/auth-attempts/${attemptId}`, "DELETE", {});
export const disconnectProvider = (providerId: string) => request<{ disconnected: true }>(`/api/model-access/providers/${providerId}`, "DELETE", {});
export const getConversation = (id: string) => request<Conversation>(`/api/conversations/${id}`);
export const reconnectConversation = (id: string) => command<Conversation>(id, { kind: "reconnect_model" });
export const switchConversationModel = (id: string, selection: ModelSelection) => command<Conversation>(id, { kind: "change_model", ...selection });
export const sendMessage = (id: string, text: string) => command<{ accepted: true; stateVersion: number }>(id, { kind: "send_message", text });
export const stopConversation = (id: string) => command<{ accepted: true }>(id, { kind: "stop" });
export const takeOver = (id: string) => command<{ controlEpoch: string }>(id, { kind: "take_control" });
export const adoptPopup = (id: string, tabId: string) => command<Conversation>(id, { kind: "adopt_popup", tabId });
export const resume = (id: string, controlEpoch: string) => command<Conversation>(id, { kind: "return_control", controlEpoch });
export const continueConversation = (id: string) => command<Conversation>(id, { kind: "continue" });
export const startOver = (id: string) => command<Conversation>(id, { kind: "start_over" });
export const resolveApproval = (id: string, approval: Approval, approved: boolean) => command<Conversation>(id, { kind: approved ? "approve" : "reject", approvalId: approval.approvalId, actionDigest: approval.actionDigest });
export const viewerToken = (id: string) => request<{ viewerPath: string }>(`/api/conversations/${id}/viewer-token`, "POST", {});
