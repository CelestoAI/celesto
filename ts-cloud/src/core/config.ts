export type FetchLike = typeof fetch;

export interface ClientConfig {
  /** Base API URL, e.g. https://api.celesto.ai */
  baseUrl?: string;
  /** Bearer token (API key or JWT). */
  token?: string;
  /** Alias for token. */
  apiKey?: string;
  /** Organization ID to send as X-Current-Organization. */
  organizationId?: string;
  /** Optional user agent for server-side requests. */
  userAgent?: string;
  /** Default request timeout in milliseconds. */
  timeoutMs?: number;
  /** Override fetch implementation (useful for testing). */
  fetch?: FetchLike;
  /** Default headers to include in every request. */
  headers?: Record<string, string>;
}

export interface RequestOptions {
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  path: string;
  query?: Record<string, string | number | boolean | undefined | null | (string | number | boolean)[]>;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export interface RequestOverrides {
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export interface RequestContext {
  fetch: FetchLike;
  baseUrl: string;
  token?: string;
  organizationId?: string;
  userAgent?: string;
  timeoutMs?: number;
  headers?: Record<string, string>;
}

export const DEFAULT_BASE_URL = "https://api.celesto.ai";

export const buildRequestContext = (config: ClientConfig): RequestContext => ({
  fetch: config.fetch ?? fetch,
  baseUrl: config.baseUrl ?? DEFAULT_BASE_URL,
  token: config.token ?? config.apiKey,
  organizationId: config.organizationId,
  userAgent: config.userAgent,
  timeoutMs: config.timeoutMs,
  headers: config.headers,
});
