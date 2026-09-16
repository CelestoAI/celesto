import { Computer, CelestoApiError, type ClientConfig } from "@celestoai/sdk";
import { SmolVM, type ComputerSessionClient, type ExecOptions, type ExecResult, type SmolVMClient } from "@celestoai/smolvm";

export type ComputerProviderId = "smolvm" | "celesto";
export type DisplayMode = "read_only" | "read_write";

export interface ComputerReference {
  provider: ComputerProviderId;
  id: string;
}

export interface OpenMuseComputer {
  readonly reference?: ComputerReference;
  exec(command: string | readonly string[], options?: ExecOptions): Promise<ExecResult>;
  createBrowserConnection(): Promise<{ url: string }>;
  createDisplayConnection(mode: DisplayMode): Promise<{ url: string }>;
  detach(): Promise<void>;
  delete(): Promise<void>;
}

export interface ComputerProvider {
  readonly id: ComputerProviderId;
  create(options: { network: "open" | "off"; viewport: { width: number; height: number } }): Promise<OpenMuseComputer>;
  reconnect(reference: ComputerReference): Promise<OpenMuseComputer | undefined>;
}

export type ComputerProviderConfig =
  | { provider: "smolvm" }
  | { provider: "celesto"; apiKey: string; apiUrl?: string };

type CloudComputer = Computer;

export interface ProviderDependencies {
  createSmolVM: () => SmolVMClient;
  createCloudComputer: (options: Parameters<typeof Computer.create>[0], config: ClientConfig) => Promise<CloudComputer>;
  getCloudComputer: (id: string, config: ClientConfig) => Promise<CloudComputer>;
  wait: (milliseconds: number) => Promise<void>;
}

const DEFAULT_DEPENDENCIES: ProviderDependencies = {
  createSmolVM: () => new SmolVM({ createTimeoutMs: 180_000 }),
  createCloudComputer: (options, config) => Computer.create(options, config) as Promise<CloudComputer>,
  getCloudComputer: (id, config) => Computer.get(id, config) as Promise<CloudComputer>,
  wait: (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds)),
};

export function computerProviderConfig(env: NodeJS.ProcessEnv = process.env): ComputerProviderConfig {
  const provider = env.OPENMUSE_COMPUTER_PROVIDER?.trim() || "smolvm";
  if (provider === "smolvm") return { provider };
  if (provider !== "celesto") {
    throw new Error("OPENMUSE_COMPUTER_PROVIDER must be 'smolvm' or 'celesto'. Set it in open-muse/.env.local, then restart OpenMuse.");
  }
  const apiKey = env.CELESTO_API_KEY?.trim();
  if (!apiKey) {
    throw new Error("Celesto Cloud is selected, but CELESTO_API_KEY is empty. Add it to open-muse/.env.local, or set OPENMUSE_COMPUTER_PROVIDER=smolvm.");
  }
  const apiUrl = env.CELESTO_API_URL?.trim();
  return { provider, apiKey, ...(apiUrl ? { apiUrl } : {}) };
}

export function createComputerProvider(
  config = computerProviderConfig(),
  dependencies: Partial<ProviderDependencies> = {},
): ComputerProvider {
  const runtime = { ...DEFAULT_DEPENDENCIES, ...dependencies };
  return config.provider === "smolvm"
    ? smolvmComputerProvider(runtime)
    : celestoComputerProvider(config, runtime);
}

function smolvmComputerProvider(runtime: ProviderDependencies): ComputerProvider {
  return {
    id: "smolvm",
    async create(options) {
      const client = runtime.createSmolVM();
      try {
        const computer = await client.computers.create({
          display: options.viewport,
          network: { mode: options.network },
        });
        return wrapSmolVMComputer(client, computer);
      } catch (error) {
        await client.close().catch(() => undefined);
        throw error;
      }
    },
    async reconnect() { return undefined; },
  };
}

function wrapSmolVMComputer(client: SmolVMClient, computer: ComputerSessionClient): OpenMuseComputer {
  let released = false;
  const release = async () => {
    if (released) return;
    released = true;
    await computer.delete().catch(() => undefined);
    await client.close();
  };
  return {
    exec: (command, options) => computer.exec(command, options),
    async createBrowserConnection() {
      if (!computer.browser.cdpUrl) await computer.browser.launch();
      const url = computer.browser.cdpUrl;
      if (!url) throw new Error("Chromium has no automation address. Stop this conversation and try again.");
      return { url };
    },
    async createDisplayConnection() {
      const target = new URL("/websockify", computer.display.viewerUrl);
      target.protocol = target.protocol === "https:" ? "wss:" : "ws:";
      return { url: target.href };
    },
    detach: release,
    delete: release,
  };
}

function celestoComputerProvider(config: Extract<ComputerProviderConfig, { provider: "celesto" }>, runtime: ProviderDependencies): ComputerProvider {
  const clientConfig: ClientConfig = { apiKey: config.apiKey, ...(config.apiUrl ? { baseUrl: config.apiUrl } : {}) };
  return {
    id: "celesto",
    async create(options) {
      const computer = await runtime.createCloudComputer({
        templateId: "browser-agent",
        networkPolicy: { mode: options.network },
      }, clientConfig);
      return wrapCloudComputer(await waitForRunning(computer, runtime), runtime);
    },
    async reconnect(reference) {
      if (reference.provider !== "celesto") return undefined;
      try {
        const computer = await runtime.getCloudComputer(reference.id, clientConfig);
        if (computer.status === "deleted" || computer.status === "deleting") return undefined;
        return wrapCloudComputer(await waitForRunning(computer, runtime), runtime);
      } catch (error) {
        if (isNotFound(error)) return undefined;
        throw error;
      }
    },
  };
}

async function waitForRunning(computer: CloudComputer, runtime: ProviderDependencies): Promise<CloudComputer> {
  const deadline = Date.now() + 180_000;
  let delay = 250;
  let started = false;
  while (computer.status !== "running") {
    if (computer.status === "deleted" || computer.status === "deleting") {
      throw Object.assign(new Error("The Celesto computer no longer exists. Continue to create a new one, or choose Start over."), { code: "computer_missing" });
    }
    if (computer.status === "error") {
      throw new Error(computer.lastError?.trim() || "The Celesto computer could not start. Stop this conversation and try again.");
    }
    if (["stopped", "restorable"].includes(computer.status) && !started) {
      started = true;
      await computer.start();
      continue;
    }
    if (Date.now() >= deadline) throw new Error("The Celesto computer did not become ready within 3 minutes. Stop this conversation and try again.");
    await runtime.wait(delay);
    delay = Math.min(delay * 2, 4_000);
    await computer.refresh();
  }
  return computer;
}

function wrapCloudComputer(computer: CloudComputer, runtime: ProviderDependencies): OpenMuseComputer {
  return {
    reference: { provider: "celesto", id: computer.id },
    async exec(command, options = {}) {
      const normalized = typeof command === "string" ? command : quoteCommand(command);
      const result = await computer.exec(normalized, {
        timeout: options.timeoutMs === undefined ? undefined : Math.max(1, Math.min(300, Math.ceil(options.timeoutMs / 1_000))),
        signal: options.signal,
      });
      return {
        ok: result.exitCode === 0,
        exitCode: result.exitCode,
        stdout: result.stdout,
        stderr: result.stderr,
        durationMs: result.durationMs ?? 0,
      };
    },
    async createBrowserConnection() {
      const connection = await createCloudConnectionWhenReady(
        () => computer.createBrowserConnection(),
        "browser",
        runtime,
      );
      return { url: connection.url };
    },
    async createDisplayConnection(mode) {
      const connection = await createCloudConnectionWhenReady(
        () => computer.createDisplayConnection({ mode }),
        "display",
        runtime,
      );
      return { url: connection.url };
    },
    async detach() {},
    async delete() {
      try {
        await computer.delete();
        const deadline = Date.now() + 60_000;
        let delay = 250;
        while (computer.status !== "deleted") {
          if (Date.now() >= deadline) throw new Error("The Celesto computer is still deleting. Retry Stop before closing OpenMuse.");
          await runtime.wait(delay);
          delay = Math.min(delay * 2, 4_000);
          try { await computer.refresh(); }
          catch (error) { if (isNotFound(error)) return; else throw error; }
        }
      }
      catch (error) { if (!isNotFound(error)) throw error; }
    },
  };
}

async function createCloudConnectionWhenReady<T>(
  connect: () => Promise<T>,
  connectionType: "browser" | "display",
  runtime: ProviderDependencies,
): Promise<T> {
  const maxAttempts = 15;
  let delay = 250;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      return await connect();
    }
    catch (error) {
      if (!isSandboxStarting(error)) throw error;
      if (attempt === maxAttempts) {
        throw new Error(`The Celesto ${connectionType} did not become ready. Stop this conversation and try again.`);
      }
      await runtime.wait(delay);
      delay = Math.min(delay * 2, 4_000);
    }
  }
  throw new Error(`The Celesto ${connectionType} did not become ready. Stop this conversation and try again.`);
}

function quoteCommand(command: readonly string[]): string {
  if (!command.length) throw new TypeError("Command argv must contain at least one item.");
  return command.map((argument) => `'${argument.replaceAll("'", `'"'"'`)}'`).join(" ");
}

function isNotFound(error: unknown): boolean {
  return error instanceof CelestoApiError && error.status === 404;
}

function isSandboxStarting(error: unknown): boolean {
  if (!(error instanceof CelestoApiError) || error.status !== 409) return false;
  const detail = typeof error.data === "object" && error.data !== null && "detail" in error.data
    ? String(error.data.detail)
    : "";
  return /sandbox is still starting/i.test(`${error.message} ${detail}`);
}
