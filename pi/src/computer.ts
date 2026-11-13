import { randomUUID } from "node:crypto";
import { readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { parse } from "dotenv";

export type ComputerStatus = string;
export interface ExecParams {
  timeout?: number;
  signal?: AbortSignal;
}
export interface ComputerExecResponse {
  exitCode: number;
  stdout: string;
  stderr: string;
  commandId?: string;
  durationMs?: number;
  timedOut?: boolean;
}
export type ComputerExecStreamEvent =
  | { type: "stdout" | "stderr"; data: string }
  | ({ type: "exit" } & Omit<ComputerExecResponse, "stdout" | "stderr">);

interface Connection {
  apiKey: string;
  origin: string;
}
interface ComputerInfo {
  id: string;
  name: string;
  status: ComputerStatus;
}
const DEFAULT_ORIGIN = "https://api.celesto.ai";
const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

async function connection(): Promise<Connection> {
  let apiKey = process.env.CELESTO_API_KEY?.trim();
  let origin = DEFAULT_ORIGIN;
  if (!apiKey) {
    try {
      apiKey = parse(
        await readFile(path.join(process.cwd(), ".env"), "utf8"),
      ).CELESTO_API_KEY?.trim();
    } catch {
      /* A project .env is optional. */
    }
  }
  if (!apiKey) {
    // Same credential file and fields as celesto.cli._credentials.read_credentials.
    try {
      const saved: unknown = JSON.parse(
        await readFile(
          path.join(os.homedir(), ".celesto", "credentials"),
          "utf8",
        ),
      );
      if (record(saved) && typeof saved.api_key === "string") {
        apiKey = saved.api_key.trim();
        if (typeof saved.base_url === "string" && saved.base_url)
          origin = saved.base_url;
      }
    } catch {
      /* Missing or unreadable saved credentials are handled below. */
    }
  }
  if (!apiKey)
    throw new Error(
      "No Celesto credentials found. Run 'celesto auth login' or set CELESTO_API_KEY.",
    );
  const url = new URL(origin);
  const local =
    url.protocol === "http:" &&
    ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
  if (
    (url.protocol !== "https:" && !local) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    url.pathname !== "/"
  ) {
    throw new Error(
      "Celesto Cloud URL must be an HTTPS origin. Run 'celesto auth login' to reconnect.",
    );
  }
  return { apiKey, origin: url.origin };
}

function computerInfo(value: unknown): ComputerInfo {
  if (
    !record(value) ||
    typeof value.id !== "string" ||
    typeof value.name !== "string" ||
    typeof value.status !== "string"
  ) {
    throw new Error(
      "Celesto returned invalid computer details. Run 'celesto computer list --cloud' and retry.",
    );
  }
  return { id: value.id, name: value.name, status: value.status };
}

export class CloudApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "CloudApiError";
  }
}

/** Pi's small Cloud transport, using the contracts maintained in celesto/_cloud.py. */
export class Computer {
  private constructor(
    private readonly connection: Connection,
    private info: ComputerInfo,
  ) {}
  get id(): string {
    return this.info.id;
  }
  get name(): string {
    return this.info.name;
  }
  get status(): ComputerStatus {
    return this.info.status;
  }

  static async create(): Promise<Computer> {
    const computer = new Computer(await connection(), {
      id: "",
      name: "",
      status: "creating",
    });
    computer.info = computerInfo(
      await computer.request(
        "POST",
        "/v1/computers",
        { external_volume_enabled: true },
        { idempotencyKey: randomUUID() },
      ),
    );
    return computer;
  }

  static async get(id: string): Promise<Computer> {
    const computer = new Computer(await connection(), {
      id,
      name: id,
      status: "unknown",
    });
    await computer.refresh();
    return computer;
  }

  private async request(
    method: string,
    route: string,
    body?: unknown,
    options: {
      signal?: AbortSignal;
      timeoutMs?: number;
      idempotencyKey?: string;
    } = {},
  ): Promise<unknown> {
    const deadline = AbortSignal.timeout(options.timeoutMs ?? 30_000);
    const signal = options.signal
      ? AbortSignal.any([options.signal, deadline])
      : deadline;
    const response = await fetch(`${this.connection.origin}${route}`, {
      method,
      signal,
      headers: {
        Authorization: `Bearer ${this.connection.apiKey}`,
        "Content-Type": "application/json",
        ...(options.idempotencyKey
          ? { "Idempotency-Key": options.idempotencyKey }
          : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await response.text();
    let data: unknown;
    try {
      data = text ? JSON.parse(text) : undefined;
    } catch {
      /* Error bodies may be plain text. */
    }
    if (!response.ok) {
      const detail =
        record(data) && typeof data.detail === "string"
          ? data.detail
          : `Celesto Cloud request failed (${response.status}).`;
      throw new CloudApiError(detail, response.status);
    }
    if (text && data === undefined)
      throw new Error(
        "Celesto returned an invalid response. Run 'celesto computer list --cloud' and retry.",
      );
    return data;
  }

  async refresh(): Promise<void> {
    this.info = computerInfo(
      await this.request("GET", `/v1/computers/${encodeURIComponent(this.id)}`),
    );
  }
  async start(): Promise<void> {
    this.info = computerInfo(
      await this.request(
        "POST",
        `/v1/computers/${encodeURIComponent(this.id)}/start`,
      ),
    );
  }
  async delete(): Promise<void> {
    await this.request(
      "DELETE",
      `/v1/computers/${encodeURIComponent(this.id)}`,
    );
    this.info = { ...this.info, status: "deleted" };
  }

  async run(
    command: string,
    params: ExecParams = {},
  ): Promise<ComputerExecResponse> {
    const timeout = params.timeout ?? 30;
    if (typeof command !== "string" || command.length > 10_000)
      throw new Error("Cloud commands allow at most 10,000 characters.");
    if (!Number.isInteger(timeout) || timeout < 1 || timeout > 300)
      throw new Error(
        "Cloud command timeout must be between 1 and 300 seconds.",
      );
    const result = await this.request(
      "POST",
      `/v1/computers/${encodeURIComponent(this.id)}/exec`,
      { command, timeout },
      { signal: params.signal, timeoutMs: (timeout + 10) * 1000 },
    );
    if (
      !record(result) ||
      typeof result.exit_code !== "number" ||
      typeof result.stdout !== "string" ||
      typeof result.stderr !== "string"
    ) {
      throw new Error(
        `Celesto returned invalid command output. Run 'celesto computer info ${this.id} --cloud' and retry.`,
      );
    }
    return {
      exitCode: result.exit_code,
      stdout: result.stdout,
      stderr: result.stderr,
      ...(typeof result.command_id === "string"
        ? { commandId: result.command_id }
        : {}),
      ...(typeof result.duration_ms === "number"
        ? { durationMs: result.duration_ms }
        : {}),
      ...(typeof result.timed_out === "boolean"
        ? { timedOut: result.timed_out }
        : {}),
    };
  }

  async *runStream(
    command: string,
    params: ExecParams = {},
  ): AsyncGenerator<ComputerExecStreamEvent> {
    const { stdout, stderr, ...exit } = await this.run(command, params);
    if (stdout) yield { type: "stdout", data: stdout };
    if (stderr) yield { type: "stderr", data: stderr };
    yield { type: "exit", ...exit };
  }
}
