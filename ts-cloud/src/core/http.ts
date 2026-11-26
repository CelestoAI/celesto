import { CelestoApiError, CelestoNetworkError } from "./errors";
import { RequestContext, RequestOptions } from "./config";

const joinUrl = (baseUrl: string, path: string): string => {
  const trimmedBase = baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${trimmedBase}${normalizedPath}`;
};

const buildQuery = (
  query?: RequestOptions["query"],
): string => {
  if (!query) {
    return "";
  }

  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) {
      continue;
    }
    if (Array.isArray(value)) {
      for (const item of value) {
        params.append(key, String(item));
      }
      continue;
    }
    params.set(key, String(value));
  }

  const serialized = params.toString();
  return serialized ? `?${serialized}` : "";
};

const parseResponseBody = async (response: Response): Promise<unknown> => {
  if (response.status === 204) {
    return undefined;
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
};

const extractErrorMessage = (data: unknown, status: number): string => {
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    if (typeof record.detail === "string") {
      return record.detail;
    }
    if (typeof record.message === "string") {
      return record.message;
    }
    if (typeof record.error === "string") {
      return record.error;
    }
  }
  return `Request failed with status ${status}`;
};

const buildRequestInit = (
  ctx: RequestContext,
  options: RequestOptions,
): { url: string; init: RequestInit } => {
  const url = `${joinUrl(ctx.baseUrl, options.path)}${buildQuery(options.query)}`;
  const headers: Record<string, string> = {
    ...(ctx.headers ?? {}),
    ...(options.headers ?? {}),
  };

  if (ctx.token) {
    headers.Authorization = `Bearer ${ctx.token}`;
  }
  if (ctx.organizationId) {
    headers["X-Current-Organization"] = ctx.organizationId;
  }
  if (ctx.userAgent && !headers["User-Agent"]) {
    headers["User-Agent"] = ctx.userAgent;
  }

  const init: RequestInit = {
    method: options.method,
    headers,
    signal: options.signal,
  };
  if (options.body !== undefined) {
    headers["Content-Type"] = headers["Content-Type"] ?? "application/json";
    init.body = headers["Content-Type"].includes("application/json")
      ? JSON.stringify(options.body)
      : (options.body as BodyInit);
  }
  return { url, init };
};

export const request = async <T>(ctx: RequestContext, options: RequestOptions): Promise<T> => {
  const { url, init } = buildRequestInit(ctx, options);
  let timeoutId: ReturnType<typeof setTimeout> | undefined;
  let controller: AbortController | undefined;

  if (!options.signal && ctx.timeoutMs && ctx.timeoutMs > 0) {
    controller = new AbortController();
    timeoutId = setTimeout(() => controller?.abort(), ctx.timeoutMs);
    init.signal = controller.signal;
  }

  try {
    const response = await ctx.fetch(url, init);
    const data = await parseResponseBody(response);

    if (!response.ok) {
      const message = extractErrorMessage(data, response.status);
      throw new CelestoApiError(
        message,
        response.status,
        data,
        response.headers.get("x-request-id") ?? undefined,
        response.headers,
      );
    }

    return data as T;
  } catch (err) {
    if (err instanceof CelestoApiError) {
      throw err;
    }
    const error = err instanceof Error ? err : new Error(String(err));
    throw new CelestoNetworkError(error.message, error);
  } finally {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  }
};

/** Make an authenticated request without consuming its response body. */
export const requestStream = async (
  ctx: RequestContext,
  options: RequestOptions,
): Promise<Response> => {
  const { url, init } = buildRequestInit(ctx, options);
  try {
    const response = await ctx.fetch(url, init);
    if (!response.ok) {
      const data = await parseResponseBody(response);
      const message = extractErrorMessage(data, response.status);
      throw new CelestoApiError(
        message,
        response.status,
        data,
        response.headers.get("x-request-id") ?? undefined,
        response.headers,
      );
    }
    return response;
  } catch (err) {
    if (err instanceof CelestoApiError) {
      throw err;
    }
    const error = err instanceof Error ? err : new Error(String(err));
    throw new CelestoNetworkError(error.message, error);
  }
};
