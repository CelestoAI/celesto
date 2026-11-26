import { randomUUID } from "node:crypto";
import { buildRequestContext, ClientConfig, RequestOverrides } from "../core/config";
import { CelestoError } from "../core/errors";
import { request } from "../core/http";
import {
  BrowserConnectionInfo,
  ComputerCommandHistoryEntry,
  ComputerCommandHistoryResponse,
  ComputerConnectionInfo,
  ComputerExecResponse,
  ComputerExecStreamEvent,
  ComputerInfo,
  ComputerListResponse,
  NetworkPolicy,
  ComputerPublishedPortInfo,
  ComputerStatus,
  CreateComputerParams,
  DisplayConnectionInfo,
  DisplayConnectionParams,
  ExecParams,
  ListCommandHistoryParams,
  ListComputersParams,
  SandboxTemplateInfo,
  TerminalSessionInfo,
} from "./types";

interface ComputerConnectionInfoWire {
  ssh?: string | null;
  access_url?: string | null;
}

interface ComputerPublishedPortInfoWire {
  id?: string | null;
  computer_id: string;
  port: number;
  url?: string | null;
  status: ComputerPublishedPortInfo["status"];
  created_at?: string | null;
}

interface ComputerInfoWire {
  network_policy?: NetworkPolicy;
  id: string;
  name: string;
  status: ComputerStatus;
  size_id?: string | null;
  vcpus: number;
  ram_mb: number;
  disk_size_mb: number;
  image: string;
  template_id: string;
  template_version?: string | null;
  external_volume_enabled?: boolean;
  connection?: ComputerConnectionInfoWire | null;
  published_ports?: ComputerPublishedPortInfoWire[];
  last_error?: string | null;
  created_at: string;
  stopped_at?: string | null;
}

interface ComputerListResponseWire {
  computers: ComputerInfoWire[];
  count: number;
}

interface ComputerExecResponseWire {
  exit_code: number;
  stdout: string;
  stderr: string;
  command_id?: string | null;
  duration_ms?: number | null;
  timed_out?: boolean | null;
}

interface ComputerCommandHistoryEntryWire {
  command_id: string;
  source: string;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  duration_ms?: number | null;
  timeout_seconds?: number | null;
  exit_code?: number | null;
  stdout_bytes?: number | null;
  stderr_bytes?: number | null;
  error_type?: string | null;
}

interface ComputerCommandHistoryResponseWire {
  commands: ComputerCommandHistoryEntryWire[];
  count: number;
}

interface TerminalConnectionInfoWire {
  terminal_id: string;
  gateway_url: string;
  token: string;
  expires_at: string;
}

interface BrowserConnectionInfoWire {
  gateway_url: string;
  token: string;
  expires_at: string;
}

interface DisplayConnectionInfoWire extends BrowserConnectionInfoWire {
  mode: DisplayConnectionInfo["mode"];
}

interface SandboxTemplateInfoWire {
  id: string;
  display_name: string;
  description: string;
  default_vcpus: number;
  default_ram_mb: number;
  default_disk_size_mb: number;
  version?: string | null;
  experimental: boolean;
}

const toConnection = (
  payload: ComputerConnectionInfoWire | null | undefined,
): ComputerConnectionInfo | undefined => {
  if (!payload) {
    return undefined;
  }
  const out: ComputerConnectionInfo = {};
  if (payload.ssh != null) {
    out.ssh = payload.ssh;
  }
  if (payload.access_url != null) {
    out.accessUrl = payload.access_url;
  }
  return out;
};

const toPublishedPortInfo = (payload: ComputerPublishedPortInfoWire): ComputerPublishedPortInfo => ({
  id: payload.id ?? null,
  computerId: payload.computer_id,
  port: payload.port,
  url: payload.url ?? null,
  status: payload.status,
  createdAt: payload.created_at ?? null,
});

const toComputerInfo = (payload: ComputerInfoWire): ComputerInfo => ({
  id: payload.id,
  name: payload.name,
  status: payload.status,
  ...(payload.size_id === undefined ? {} : { sizeId: payload.size_id }),
  vcpus: payload.vcpus,
  ramMb: payload.ram_mb,
  diskSizeMb: payload.disk_size_mb,
  image: payload.image,
  templateId: payload.template_id,
  templateVersion: payload.template_version ?? null,
  persistentHome: payload.external_volume_enabled ?? false,
  networkPolicy: payload.network_policy ?? { mode: "open" },
  connection: toConnection(payload.connection),
  publishedPorts: payload.published_ports?.map(toPublishedPortInfo),
  lastError: payload.last_error ?? null,
  createdAt: payload.created_at,
  stoppedAt: payload.stopped_at ?? null,
});

const toExecResponse = (payload: ComputerExecResponseWire): ComputerExecResponse => {
  const response: ComputerExecResponse = {
    exitCode: payload.exit_code,
    stdout: payload.stdout,
    stderr: payload.stderr,
  };
  if (payload.command_id !== undefined) response.commandId = payload.command_id;
  if (payload.duration_ms !== undefined) response.durationMs = payload.duration_ms;
  if (payload.timed_out !== undefined) response.timedOut = payload.timed_out;
  return response;
};

const toCommandHistoryEntry = (
  payload: ComputerCommandHistoryEntryWire,
): ComputerCommandHistoryEntry => ({
  commandId: payload.command_id,
  source: payload.source,
  status: payload.status,
  startedAt: payload.started_at,
  endedAt: payload.ended_at,
  durationMs: payload.duration_ms,
  timeoutSeconds: payload.timeout_seconds,
  exitCode: payload.exit_code,
  stdoutBytes: payload.stdout_bytes,
  stderrBytes: payload.stderr_bytes,
  errorType: payload.error_type,
});

function authenticatedGatewayUrl(gatewayUrl: string, token: string): string {
  const separator = gatewayUrl.includes("?") ? "&" : "?";
  return `${gatewayUrl}${separator}token=${encodeURIComponent(token)}`;
}

const toTerminalConnectionInfo = (
  payload: TerminalConnectionInfoWire,
): TerminalSessionInfo => {
  return {
    terminalId: payload.terminal_id,
    gatewayUrl: payload.gateway_url,
    url: authenticatedGatewayUrl(payload.gateway_url, payload.token),
    token: payload.token,
    expiresAt: payload.expires_at,
    headers: {},
    firstMessage: "",
  };
};

const toBrowserConnectionInfo = (
  payload: unknown,
): BrowserConnectionInfo => {
  if (
    typeof payload !== "object" ||
    payload === null ||
    typeof (payload as Partial<BrowserConnectionInfoWire>).gateway_url !== "string" ||
    typeof (payload as Partial<BrowserConnectionInfoWire>).token !== "string" ||
    typeof (payload as Partial<BrowserConnectionInfoWire>).expires_at !== "string"
  ) {
    throw new CelestoError(
      "Celesto did not return browser connection details. Call createBrowserConnection() again.",
    );
  }
  const connection = payload as BrowserConnectionInfoWire;
  return {
    gatewayUrl: connection.gateway_url,
    url: authenticatedGatewayUrl(connection.gateway_url, connection.token),
    token: connection.token,
    expiresAt: connection.expires_at,
  };
};

const toDisplayConnectionInfo = (
  payload: unknown,
): DisplayConnectionInfo => {
  if (
    typeof payload !== "object" ||
    payload === null ||
    ((payload as Partial<DisplayConnectionInfoWire>).mode !== "read_only" &&
      (payload as Partial<DisplayConnectionInfoWire>).mode !== "read_write")
  ) {
    throw new CelestoError(
      "Celesto did not return display connection details. Call createDisplayConnection() again.",
    );
  }
  const connection = payload as DisplayConnectionInfoWire;
  try {
    return { ...toBrowserConnectionInfo(connection), mode: connection.mode };
  } catch {
    throw new CelestoError(
      "Celesto did not return display connection details. Call createDisplayConnection() again.",
    );
  }
};

const toSandboxTemplateInfo = (payload: SandboxTemplateInfoWire): SandboxTemplateInfo => ({
  id: payload.id,
  displayName: payload.display_name,
  description: payload.description,
  defaultVcpus: payload.default_vcpus,
  defaultRamMb: payload.default_ram_mb,
  defaultDiskSizeMb: payload.default_disk_size_mb,
  version: payload.version ?? null,
  experimental: payload.experimental,
});

const resourceOverrides = ["cpus", "vcpus", "memory", "ramMb", "disk", "diskSizeMb"] as const;
const createOptions = new Set<string>([
  "sizeId", "idempotencyKey", "networkPolicy", "image", "templateId", "templateVersion",
  "persistentHome", ...resourceOverrides,
] satisfies (keyof CreateComputerParams)[]);

const buildCreateComputerBody = (params: CreateComputerParams): Record<string, unknown> => {
  for (const field of Object.keys(params)) {
    if (field === "size" || field === "size_id") {
      throw new TypeError(`${field} is not a Cloud computer create option. Use sizeId instead.`);
    }
    if (!createOptions.has(field)) {
      throw new TypeError(`Unknown computer create option ${JSON.stringify(field)}. Remove it and retry.`);
    }
  }
  if (resourceOverrides.some((field) => params[field] !== undefined)) {
    throw new TypeError("Cloud computers do not accept CPU, memory, or disk overrides. Use sizeId instead.");
  }

  const body: Record<string, unknown> = {};
  if (params.sizeId !== undefined) {
    if (typeof params.sizeId !== "string" || !params.sizeId.trim() || params.sizeId.length > 32) {
      throw new TypeError('Choose a sizeId of 1–32 characters, such as "micro".');
    }
    body.size_id = params.sizeId;
  }
  if (params.networkPolicy !== undefined) {
    const policy = params.networkPolicy;
    if (!policy || Object.keys(policy).length !== 1 || !("mode" in policy) || !["open", "off"].includes(policy.mode)) {
      throw new Error('networkPolicy must be {mode: "open"} or {mode: "off"}.');
    }
    if (policy.mode === "off" && params.persistentHome) {
      throw new Error("External volumes require internet access; set persistentHome=false.");
    }
    body.network_policy = { mode: policy.mode };
  }
  if (params.image !== undefined) {
    body.image = params.image;
  }
  if (params.templateId !== undefined) {
    body.template_id = params.templateId;
  }
  if (params.templateVersion !== undefined) {
    body.template_version = params.templateVersion;
  }
  if (params.persistentHome !== undefined) {
    body.external_volume_enabled = params.persistentHome;
  }
  return body;
};

const computersPath = (path: string): string => `/v1/computers${path}`;

const pickOverrides = (options?: RequestOverrides): RequestOverrides => ({
  headers: options?.headers,
  signal: options?.signal,
});

const createManagedSignal = (
  signal: AbortSignal | undefined,
  timeoutMs: number | undefined,
): { signal: AbortSignal | undefined; cleanup: () => void } => {
  if (!timeoutMs || timeoutMs <= 0) {
    return { signal, cleanup: () => {} };
  }

  const controller = new AbortController();
  const abort = () => controller.abort();
  if (signal?.aborted) {
    abort();
  } else {
    signal?.addEventListener("abort", abort, { once: true });
  }
  const timer = setTimeout(abort, timeoutMs);

  return {
    signal: controller.signal,
    cleanup: () => {
      clearTimeout(timer);
      signal?.removeEventListener("abort", abort);
    },
  };
};

/**
 * Client for managing sandboxed computers (AI sandboxes).
 *
 * Provides computer lifecycle, buffered command execution,
 * command history, published ports, and direct terminal gateway sessions.
 *
 * @example
 * ```ts
 * const computer = await Computer.create();
 * const result = await computer.run("uname -a");
 * console.log(result.stdout);
 * await computer.delete();
 * ```
 */
export class ComputersClient {
  private readonly config: ClientConfig;

  constructor(config: ClientConfig) {
    this.config = config;
  }

  async create(params: CreateComputerParams = {}, options?: RequestOverrides): Promise<ComputerInfo> {
    const ctx = buildRequestContext(this.config);
    // Preserve explicit headers while ensuring Fetch receives exactly one key.
    const headers: Record<string, string> = {};
    let suppliedKey: string | undefined;
    for (const source of [ctx.headers, options?.headers]) {
      for (const [name, value] of Object.entries(source ?? {})) {
        if (name.toLowerCase() === "idempotency-key") suppliedKey = value;
        else headers[name] = value;
      }
    }
    const key = params.idempotencyKey ?? suppliedKey ?? randomUUID();
    if (typeof key !== "string" || !key.trim()) {
      throw new TypeError("idempotencyKey must not be empty. Omit it to generate a key.");
    }
    headers["Idempotency-Key"] = key;
    const data = await request<ComputerInfoWire>({ ...ctx, headers: undefined }, {
      method: "POST",
      path: computersPath(""),
      body: buildCreateComputerBody(params),
      headers,
      signal: options?.signal,
    });
    return toComputerInfo(data);
  }

  async listTemplates(options?: RequestOverrides): Promise<SandboxTemplateInfo[]> {
    const ctx = buildRequestContext(this.config);
    const data = await request<SandboxTemplateInfoWire[]>(ctx, {
      method: "GET",
      path: computersPath("/templates"),
      ...pickOverrides(options),
    });
    return data.map(toSandboxTemplateInfo);
  }

  async list(params: ListComputersParams = {}, options?: RequestOverrides): Promise<ComputerListResponse> {
    const ctx = buildRequestContext(this.config);
    const data = await request<ComputerListResponseWire>(ctx, {
      method: "GET",
      path: computersPath(""),
      query: {
        status: params.status,
        template_id: params.templateId,
        project_id: params.projectId,
        limit: params.limit,
      },
      ...pickOverrides(options),
    });
    return {
      computers: data.computers.map(toComputerInfo),
      count: data.count,
    };
  }

  async get(computerId: string, options?: RequestOverrides): Promise<ComputerInfo> {
    const ctx = buildRequestContext(this.config);
    const data = await request<ComputerInfoWire>(ctx, {
      method: "GET",
      path: computersPath(`/${encodeURIComponent(computerId)}`),
      ...pickOverrides(options),
    });
    return toComputerInfo(data);
  }

  async exec(
    computerId: string,
    command: string,
    params: ExecParams = {},
    options?: RequestOverrides,
  ): Promise<ComputerExecResponse> {
    if (typeof command !== "string" || command.length === 0) {
      throw new TypeError("Provide a non-empty command to run on the Cloud computer.");
    }
    if (command.length > 10_000) {
      // The Cloud API counts Unicode characters, not JavaScript UTF-16 units.
      let count = 0;
      for (const _ of command) {
        if (++count > 10_000) {
          throw new TypeError("Cloud commands allow at most 10,000 characters. Shorten the command and retry.");
        }
      }
    }
    const timeout = params.timeout ?? 30;
    if (!Number.isInteger(timeout) || timeout < 1 || timeout > 300) {
      throw new TypeError("Choose a whole-number command timeout between 1 and 300 seconds.");
    }
    const ctx = buildRequestContext(this.config);
    const managedSignal = createManagedSignal(
      params.signal ?? options?.signal,
      this.config.timeoutMs,
    );
    try {
      const data = await request<ComputerExecResponseWire>(ctx, {
        method: "POST",
        path: computersPath(`/${encodeURIComponent(computerId)}/exec`),
        body: {
          command,
          timeout,
        },
        headers: options?.headers,
        signal: managedSignal.signal,
      });
      return toExecResponse(data);
    } finally {
      managedSignal.cleanup();
    }
  }

  /** Yield output and exit events after the command has finished. */
  async *execStream(
    computerId: string,
    command: string,
    params: ExecParams = {},
    options?: RequestOverrides,
  ): AsyncGenerator<ComputerExecStreamEvent> {
    const { stdout, stderr, exitCode, commandId, durationMs, timedOut } =
      await this.exec(computerId, command, params, options);
    if (stdout) yield { type: "stdout", data: stdout };
    if (stderr) yield { type: "stderr", data: stderr };
    yield {
      type: "exit",
      exitCode,
      ...(commandId == null ? {} : { commandId }),
      ...(durationMs == null ? {} : { durationMs }),
      ...(timedOut == null ? {} : { timedOut }),
    };
  }

  async listCommandHistory(
    computerId: string,
    params: ListCommandHistoryParams = {},
    options?: RequestOverrides,
  ): Promise<ComputerCommandHistoryResponse> {
    const ctx = buildRequestContext(this.config);
    const data = await request<ComputerCommandHistoryResponseWire>(ctx, {
      method: "GET",
      path: computersPath(`/${encodeURIComponent(computerId)}/commands`),
      query: { limit: params.limit },
      ...pickOverrides(options),
    });
    return {
      commands: data.commands.map(toCommandHistoryEntry),
      count: data.count,
    };
  }

  async stop(computerId: string, options?: RequestOverrides): Promise<ComputerInfo> {
    const ctx = buildRequestContext(this.config);
    const data = await request<ComputerInfoWire>(ctx, {
      method: "POST",
      path: computersPath(`/${encodeURIComponent(computerId)}/stop`),
      ...pickOverrides(options),
    });
    return toComputerInfo(data);
  }

  async start(computerId: string, options?: RequestOverrides): Promise<ComputerInfo> {
    const ctx = buildRequestContext(this.config);
    const data = await request<ComputerInfoWire>(ctx, {
      method: "POST",
      path: computersPath(`/${encodeURIComponent(computerId)}/start`),
      ...pickOverrides(options),
    });
    return toComputerInfo(data);
  }

  async delete(computerId: string, options?: RequestOverrides): Promise<ComputerInfo> {
    const ctx = buildRequestContext(this.config);
    const data = await request<ComputerInfoWire>(ctx, {
      method: "DELETE",
      path: computersPath(`/${encodeURIComponent(computerId)}`),
      ...pickOverrides(options),
    });
    return toComputerInfo(data);
  }

  async publishPort(
    computerId: string,
    port = 8000,
    options?: RequestOverrides,
  ): Promise<ComputerPublishedPortInfo> {
    const ctx = buildRequestContext(this.config);
    const data = await request<ComputerPublishedPortInfoWire>(ctx, {
      method: "POST",
      path: computersPath(`/${encodeURIComponent(computerId)}/published-ports`),
      body: { port },
      ...pickOverrides(options),
    });
    return toPublishedPortInfo(data);
  }

  async listPublishedPorts(
    computerId: string,
    options?: RequestOverrides,
  ): Promise<ComputerPublishedPortInfo[]> {
    const ctx = buildRequestContext(this.config);
    const data = await request<ComputerPublishedPortInfoWire[]>(ctx, {
      method: "GET",
      path: computersPath(`/${encodeURIComponent(computerId)}/published-ports`),
      ...pickOverrides(options),
    });
    return data.map(toPublishedPortInfo);
  }

  async unpublishPort(
    computerId: string,
    port = 8000,
    options?: RequestOverrides,
  ): Promise<ComputerPublishedPortInfo> {
    const ctx = buildRequestContext(this.config);
    const data = await request<ComputerPublishedPortInfoWire>(ctx, {
      method: "DELETE",
      path: computersPath(`/${encodeURIComponent(computerId)}/published-ports/${port}`),
      ...pickOverrides(options),
    });
    return toPublishedPortInfo(data);
  }

  /** Create a short-lived direct connection to Celesto's terminal gateway. */
  async createTerminalSession(
    computerIdOrName: string,
    options?: RequestOverrides,
  ): Promise<TerminalSessionInfo> {
    const ctx = buildRequestContext(this.config);
    const data = await request<TerminalConnectionInfoWire>(ctx, {
      method: "POST",
      path: computersPath(`/${encodeURIComponent(computerIdOrName)}/terminals`),
      ...pickOverrides(options),
    });
    return toTerminalConnectionInfo(data);
  }

  /** Create a short-lived CDP connection for browser automation. */
  async createBrowserConnection(
    computerIdOrName: string,
    options?: RequestOverrides,
  ): Promise<BrowserConnectionInfo> {
    const ctx = buildRequestContext(this.config);
    const data = await request<BrowserConnectionInfoWire>(ctx, {
      method: "POST",
      path: computersPath(`/${encodeURIComponent(computerIdOrName)}/browser`),
      ...pickOverrides(options),
    });
    return toBrowserConnectionInfo(data);
  }

  /** Create a short-lived RFB connection to watch or control the graphical display. */
  async createDisplayConnection(
    computerIdOrName: string,
    params: DisplayConnectionParams = {},
    options?: RequestOverrides,
  ): Promise<DisplayConnectionInfo> {
    const ctx = buildRequestContext(this.config);
    const data = await request<DisplayConnectionInfoWire>(ctx, {
      method: "POST",
      path: computersPath(`/${encodeURIComponent(computerIdOrName)}/display`),
      body: params.mode === undefined ? undefined : { mode: params.mode },
      ...pickOverrides(options),
    });
    return toDisplayConnectionInfo(data);
  }

  /** @deprecated Use createTerminalSession(). */
  async getTerminalConnection(
    computerIdOrName: string,
    options?: RequestOverrides,
  ): Promise<TerminalSessionInfo> {
    return this.createTerminalSession(computerIdOrName, options);
  }
}
