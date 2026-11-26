export type ComputerStatus =
  | "creating"
  | "running"
  | "stopping"
  | "stopped"
  | "starting"
  | "restoring"
  | "restorable"
  | "deleting"
  | "deleted"
  | "error";

export interface ComputerConnectionInfo {
  ssh?: string;
  accessUrl?: string;
}

export type PublishedPortStatus =
  | "publishing"
  | "published"
  | "unpublishing"
  | "unpublished"
  | "error";

export interface ComputerPublishedPortInfo {
  id?: string | null;
  computerId: string;
  port: number;
  url?: string | null;
  status: PublishedPortStatus;
  createdAt?: string | null;
}

export interface NetworkPolicy {
  mode: "open" | "off";
}

export interface ComputerInfo {
  networkPolicy?: NetworkPolicy;
  id: string;
  name: string;
  status: ComputerStatus;
  /** Named Cloud size, when provided by the API. */
  sizeId?: string | null;
  vcpus: number;
  ramMb: number;
  diskSizeMb: number;
  image: string;
  templateId: string;
  templateVersion?: string | null;
  /** Whether /home/ohm survives stop and restore. */
  persistentHome: boolean;
  connection?: ComputerConnectionInfo;
  publishedPorts?: ComputerPublishedPortInfo[];
  lastError?: string | null;
  createdAt: string;
  stoppedAt?: string | null;
}

export interface ComputerListResponse {
  computers: ComputerInfo[];
  count: number;
}

export interface ListComputersParams {
  /** Optional status filter, such as "running" or "stopped". */
  status?: ComputerStatus;
  /** Optional template filter, such as "coding-agent". */
  templateId?: string;
  /** Optional project ID filter. */
  projectId?: string;
  /** Optional maximum number of computers to return. */
  limit?: number;
}

export interface ComputerExecResponse {
  exitCode: number;
  stdout: string;
  stderr: string;
  commandId?: string | null;
  durationMs?: number | null;
  timedOut?: boolean | null;
}

/** Cloud command iterators yield output and exit events after completion. */
export type ComputerExecStreamEvent =
  | {
      /** Legacy event kept for source compatibility; Cloud does not emit it. */
      type: "started";
      commandId: string;
      startedAtUnixMs: number;
      timeoutSeconds: number;
    }
  | {
      type: "stdout" | "stderr";
      data: string;
    }
  | {
      type: "exit";
      exitCode: number;
      commandId?: string;
      startedAtUnixMs?: number;
      endedAtUnixMs?: number;
      durationMs?: number;
      timedOut?: boolean;
    };

export interface ComputerCommandHistoryEntry {
  commandId: string;
  source: string;
  status: string;
  startedAt?: string | null;
  endedAt?: string | null;
  durationMs?: number | null;
  timeoutSeconds?: number | null;
  exitCode?: number | null;
  stdoutBytes?: number | null;
  stderrBytes?: number | null;
  errorType?: string | null;
}

export interface ComputerCommandHistoryResponse {
  commands: ComputerCommandHistoryEntry[];
  count: number;
}

export interface SandboxTemplateInfo {
  id: string;
  displayName: string;
  description: string;
  defaultVcpus: number;
  defaultRamMb: number;
  defaultDiskSizeMb: number;
  version?: string | null;
  experimental: boolean;
}

export interface CreateComputerParams {
  /** Stable key for retrying the same create request. Defaults to a new key. */
  idempotencyKey?: string;
  /** Named Cloud size (for example, "micro"). Omit for your account's default. */
  sizeId?: string;
  /** Outbound internet access, fixed at creation. Defaults to open. */
  networkPolicy?: NetworkPolicy;
  /** @deprecated Cloud does not support CPU overrides. Use sizeId. */
  cpus?: number;
  /** @deprecated Cloud does not support CPU overrides. Use sizeId. */
  vcpus?: number;
  /** @deprecated Cloud does not support memory overrides. Use sizeId. */
  memory?: number;
  /** @deprecated Cloud does not support memory overrides. Use sizeId. */
  ramMb?: number;
  /** @deprecated Cloud does not support disk overrides. Use sizeId. */
  disk?: number | string;
  /** @deprecated Cloud does not support disk overrides. Use sizeId. */
  diskSizeMb?: number;
  /** Legacy OS image selector. */
  image?: string;
  /** Sandbox template id, such as "scratch" or "coding-agent". */
  templateId?: string;
  /** Optional immutable template version. */
  templateVersion?: string;
  /** Request a separate home volume, if supported. Not available on pool computers. */
  persistentHome?: boolean;
}

export interface ExecParams {
  /** Timeout in seconds (1-300). Defaults to 30. */
  timeout?: number;
  /** Abort the HTTP request. This does not guarantee that the command stops. */
  signal?: AbortSignal;
}

export interface ListCommandHistoryParams {
  /** Maximum command records to return (1-200). Defaults to 50. */
  limit?: number;
}

/** Legacy WebSocket connection fields retained for source compatibility. */
export interface TerminalConnectionInfo {
  /** Authenticated wss:// URL ready to pass to a WebSocket constructor. */
  url: string;
  /** @deprecated The fast terminal gateway does not require custom headers. */
  headers: Record<string, string>;
  /** @deprecated The fast terminal gateway does not require a first message. */
  firstMessage: string;
}

/** A short-lived direct connection to Celesto's fast terminal gateway. */
export interface TerminalSessionInfo extends TerminalConnectionInfo {
  /** Durable terminal session ID. */
  terminalId: string;
  /** Gateway URL without credentials. */
  gatewayUrl: string;
  /** Short-lived terminal token. Treat this value as a secret. */
  token: string;
  /** ISO 8601 expiry time for the terminal token. */
  expiresAt: string;
}

export interface BrowserConnectionInfo {
  /** Authenticated CDP WebSocket URL ready for a browser automation client. */
  url: string;
  /** Gateway URL without credentials. */
  gatewayUrl: string;
  /** Short-lived browser connection token. Treat this value as a secret. */
  token: string;
  /** ISO 8601 expiry time for the browser token. */
  expiresAt: string;
}

export type DisplayConnectionMode = "read_only" | "read_write";

export interface DisplayConnectionParams {
  /** Watch the display, or also allow pointer and keyboard input. Defaults to read_only. */
  mode?: DisplayConnectionMode;
}

export interface DisplayConnectionInfo {
  /** Authenticated RFB WebSocket URL ready for an RFB/noVNC client. */
  url: string;
  /** Gateway URL without credentials. */
  gatewayUrl: string;
  /** Short-lived display connection token. Treat this value as a secret. */
  token: string;
  /** ISO 8601 expiry time for the display token. */
  expiresAt: string;
  /** Whether this connection can only watch or can also control the display. */
  mode: DisplayConnectionMode;
}
