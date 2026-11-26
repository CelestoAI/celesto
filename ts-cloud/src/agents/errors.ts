/**
 * Typed errors for managed agents.
 *
 * A refused run comes back with a machine-readable code, so your code can
 * branch on *why* instead of matching message text. Each code gets its own
 * class here; all of them are still `CelestoApiError`, so existing
 * `catch (e) { if (e instanceof CelestoApiError) ... }` keeps working.
 *
 * Two error body shapes exist in the wild:
 *
 * ```json
 * {"detail": "Agent not found"}
 * {"detail": {"code": "budget_exceeded", "message": "..."}}
 * ```
 */

import { CelestoApiError } from "../core/errors";

/** Every reason a managed-agent request can be refused. */
export type RunErrorCode =
  | "budget_exceeded"
  | "session_busy"
  | "idempotency_conflict"
  | "agent_archived"
  | "provider_not_connected"
  | "session_agent_mismatch"
  | "session_end_user_mismatch"
  | "model_requires_own_key"
  | "config_key_not_allowed";

/** A managed-agent request was refused with a known error code. */
export class ManagedAgentError extends CelestoApiError {
  /** The API's error code, such as `"budget_exceeded"`. */
  readonly code?: RunErrorCode;
  /** Seconds to wait before retrying, when the API said so. */
  readonly retryAfter?: number;
  /** True when retrying the identical request can succeed. */
  readonly retryable: boolean = false;

  constructor(
    message: string,
    status: number,
    data: unknown,
    options: { code?: RunErrorCode; retryAfter?: number; requestId?: string; headers?: Headers } = {},
  ) {
    super(message, status, data, options.requestId, options.headers);
    this.name = "ManagedAgentError";
    this.code = options.code;
    this.retryAfter = options.retryAfter;
  }
}

/**
 * 402 — this end user's budget is spent for the current window.
 *
 * Raise the cap with `endUsers.update(id, { budgetCapUsd })`, or wait for
 * `budget.windowResetsAt`.
 */
export class BudgetExceededError extends ManagedAgentError {
  constructor(...args: ConstructorParameters<typeof ManagedAgentError>) {
    super(...args);
    this.name = "BudgetExceededError";
  }
}

/**
 * 409 — another run holds this session. Retryable.
 *
 * `retryAfter` carries the API's hint in seconds. Sessions run one at a time,
 * so the same request succeeds once the in-flight run settles.
 */
export class SessionBusyError extends ManagedAgentError {
  override readonly retryable = true;

  constructor(...args: ConstructorParameters<typeof ManagedAgentError>) {
    super(...args);
    this.name = "SessionBusyError";
  }
}

/** 409 — this idempotency key was already used with a different body. */
export class IdempotencyConflictError extends ManagedAgentError {
  constructor(...args: ConstructorParameters<typeof ManagedAgentError>) {
    super(...args);
    this.name = "IdempotencyConflictError";
  }
}

/** 409 — the agent is archived and cannot take new runs. */
export class AgentArchivedError extends ManagedAgentError {
  constructor(...args: ConstructorParameters<typeof ManagedAgentError>) {
    super(...args);
    this.name = "AgentArchivedError";
  }
}

/** 409 — no provider credential is connected for this agent's model. */
export class ProviderNotConnectedError extends ManagedAgentError {
  constructor(...args: ConstructorParameters<typeof ManagedAgentError>) {
    super(...args);
    this.name = "ProviderNotConnectedError";
  }
}

/** 409 — that session belongs to a different agent. */
export class SessionAgentMismatchError extends ManagedAgentError {
  constructor(...args: ConstructorParameters<typeof ManagedAgentError>) {
    super(...args);
    this.name = "SessionAgentMismatchError";
  }
}

/**
 * 422 — that session belongs to a different end user.
 *
 * Sessions are owned by one end user. Pass the session's own `endUserId`, or
 * omit `sessionId` to start a new session.
 */
export class SessionEndUserMismatchError extends ManagedAgentError {
  constructor(...args: ConstructorParameters<typeof ManagedAgentError>) {
    super(...args);
    this.name = "SessionEndUserMismatchError";
  }
}

/** 422 — this model can only run on your own provider key. */
export class ModelRequiresOwnKeyError extends ManagedAgentError {
  constructor(...args: ConstructorParameters<typeof ManagedAgentError>) {
    super(...args);
    this.name = "ModelRequiresOwnKeyError";
  }
}

/** 422 — the agent config carried a key outside {@link AgentConfig}. */
export class ConfigKeyNotAllowedError extends ManagedAgentError {
  constructor(...args: ConstructorParameters<typeof ManagedAgentError>) {
    super(...args);
    this.name = "ConfigKeyNotAllowedError";
  }
}

const ERROR_CLASSES: Record<RunErrorCode, typeof ManagedAgentError> = {
  budget_exceeded: BudgetExceededError,
  session_busy: SessionBusyError,
  idempotency_conflict: IdempotencyConflictError,
  agent_archived: AgentArchivedError,
  provider_not_connected: ProviderNotConnectedError,
  session_agent_mismatch: SessionAgentMismatchError,
  session_end_user_mismatch: SessionEndUserMismatchError,
  model_requires_own_key: ModelRequiresOwnKeyError,
  config_key_not_allowed: ConfigKeyNotAllowedError,
};

/** Statuses only managed agents use, when the body carries no known code. */
const STATUS_FALLBACK: Record<number, typeof ManagedAgentError> = {
  402: BudgetExceededError,
};

const readErrorCode = (data: unknown): RunErrorCode | undefined => {
  if (!data || typeof data !== "object") return undefined;
  const record = data as Record<string, unknown>;
  const detail = record.detail;
  const raw =
    detail && typeof detail === "object"
      ? (detail as Record<string, unknown>).code
      : record.code;
  if (typeof raw !== "string") return undefined;
  return raw in ERROR_CLASSES ? (raw as RunErrorCode) : undefined;
};

const readMessage = (data: unknown, fallback: string): string => {
  if (data && typeof data === "object") {
    const detail = (data as Record<string, unknown>).detail;
    if (detail && typeof detail === "object") {
      const message = (detail as Record<string, unknown>).message;
      if (typeof message === "string") return message;
    }
  }
  return fallback;
};

const readRetryAfter = (headers: Headers | undefined): number | undefined => {
  const raw = headers?.get("retry-after");
  if (!raw) return undefined;
  const seconds = Number(raw);
  // Retry-After may also be an HTTP date; we do not guess at clock skew.
  return Number.isFinite(seconds) ? seconds : undefined;
};

/**
 * Re-throwable: turn a generic API error into its specific type.
 *
 * Anything that is not a recognized managed-agent refusal is returned
 * unchanged, so network errors and plain 404s keep their existing shape.
 */
export const toManagedAgentError = (error: unknown): unknown => {
  if (!(error instanceof CelestoApiError) || error instanceof ManagedAgentError) {
    return error;
  }

  const code = readErrorCode(error.data);
  const ErrorClass = (code && ERROR_CLASSES[code]) ?? STATUS_FALLBACK[error.status];
  if (!ErrorClass) return error;

  return new ErrorClass(readMessage(error.data, error.message), error.status, error.data, {
    code: code ?? (error.status === 402 ? "budget_exceeded" : undefined),
    retryAfter: readRetryAfter(error.headers),
    requestId: error.requestId,
    headers: error.headers,
  });
};
