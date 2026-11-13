import os from "node:os";
import path from "node:path";

import type {
  ExtensionAPI,
  ExtensionContext,
  SessionStartEvent,
} from "@earendil-works/pi-coding-agent";
import {
  createBashTool,
  createEditTool,
  createReadTool,
  createWriteTool,
} from "@earendil-works/pi-coding-agent";
import { Computer, CloudApiError, type ComputerStatus } from "./computer.js";

import {
  createCelestoBashOperations,
  createCelestoEditOperations,
  createCelestoReadOperations,
  createCelestoWriteOperations,
  prepareRemoteWorkspace,
  REMOTE_WORKSPACE_DISPLAY,
} from "./operations.js";
import {
  syncWorkspace,
  type SyncResult,
  uploadInitialWorkspace,
  type WorkspaceRevision,
} from "./workspace.js";

const STATE_ENTRY = "celesto-pi-state";
const STATE_VERSION = 1;

interface CelestoSessionState {
  version: 1;
  computerId: string;
  computerName: string;
  owned: boolean;
  keep: boolean;
  localRoot: string;
  revision?: WorkspaceRevision;
}

interface RuntimeState extends CelestoSessionState {
  computer: Computer;
  remoteWorkspace: string;
}

function isPersistedState(value: unknown): value is CelestoSessionState {
  if (!value || typeof value !== "object") return false;
  const state = value as Partial<CelestoSessionState>;
  return (
    state.version === STATE_VERSION &&
    typeof state.computerId === "string" &&
    typeof state.computerName === "string" &&
    typeof state.owned === "boolean" &&
    typeof state.keep === "boolean" &&
    typeof state.localRoot === "string"
  );
}

function restoreSessionState(
  ctx: ExtensionContext,
): CelestoSessionState | undefined {
  const entries = ctx.sessionManager.getBranch();
  for (let index = entries.length - 1; index >= 0; index -= 1) {
    const entry = entries[index];
    if (
      entry?.type === "custom" &&
      entry.customType === STATE_ENTRY &&
      isPersistedState(entry.data)
    ) {
      return entry.data;
    }
  }
  return undefined;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function sleep(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

export function assertSafeLocalRoot(localRoot: string): void {
  const resolved = path.resolve(localRoot);
  const filesystemRoot = path.parse(resolved).root;
  if (resolved !== filesystemRoot && resolved !== path.resolve(os.homedir()))
    return;

  throw new Error(
    `Refusing to copy ${JSON.stringify(resolved)}. Exit Pi, change to a project directory, restart with pi --celesto, then run /celesto push.`,
  );
}

async function ensureComputerRunning(computer: Computer): Promise<void> {
  const terminalStatuses: ComputerStatus[] = ["deleted", "deleting", "error"];
  if (terminalStatuses.includes(computer.status)) {
    throw new Error(
      `Computer "${computer.name}" is ${computer.status}. Choose a running computer with --celesto-computer or omit the flag to create one.`,
    );
  }
  if (computer.status === "stopped" || computer.status === "restorable") {
    await computer.start();
  }

  const deadline = Date.now() + 120_000;
  while (computer.status !== "running") {
    if (Date.now() >= deadline) {
      throw new Error(
        `Computer "${computer.name}" did not become ready. Check it with celesto computer list --cloud, then retry.`,
      );
    }
    await sleep(1_000);
    await computer.refresh();
    if (terminalStatuses.includes(computer.status)) {
      throw new Error(
        `Computer "${computer.name}" is ${computer.status}. Check it with celesto computer list --cloud, then retry.`,
      );
    }
  }
}

export default function celestoPiExtension(pi: ExtensionAPI): void {
  pi.registerFlag("celesto", {
    description: "Run Pi coding tools in a Celesto computer",
    type: "boolean",
    default: false,
  });
  pi.registerFlag("celesto-computer", {
    description: "Reuse a Celesto computer by name or ID",
    type: "string",
  });

  const registrationRoot = process.cwd();
  const localRead = createReadTool(registrationRoot);
  const localWrite = createWriteTool(registrationRoot);
  const localEdit = createEditTool(registrationRoot);
  const localBash = createBashTool(registrationRoot);

  let modeEnabled = false;
  let runtime: RuntimeState | undefined;
  let starting: Promise<RuntimeState> | undefined;
  let startupError: Error | undefined;
  let syncing: Promise<SyncResult> | undefined;
  let workspaceOperation: Promise<unknown> | undefined;

  const persist = (state: RuntimeState): void => {
    const {
      computer: _computer,
      remoteWorkspace: _remoteWorkspace,
      ...saved
    } = state;
    pi.appendEntry<CelestoSessionState>(STATE_ENTRY, saved);
  };

  const updateStatus = (ctx: ExtensionContext, detail?: string): void => {
    if (!runtime) {
      ctx.ui.setStatus("celesto", undefined);
      return;
    }
    const suffix = detail ? ` · ${detail}` : "";
    ctx.ui.setStatus(
      "celesto",
      ctx.ui.theme.fg(
        "accent",
        `Celesto: ${runtime.computerName}:${REMOTE_WORKSPACE_DISPLAY}${suffix}`,
      ),
    );
  };

  async function initialize(
    event: SessionStartEvent,
    ctx: ExtensionContext,
  ): Promise<RuntimeState | undefined> {
    const saved = restoreSessionState(ctx);
    const selected = pi.getFlag("celesto-computer") as string | undefined;
    const enabled = Boolean(pi.getFlag("celesto") || selected || saved);
    modeEnabled = enabled;
    if (!enabled) return undefined;

    ctx.ui.setStatus(
      "celesto",
      ctx.ui.theme.fg("muted", "Celesto: connecting"),
    );
    let computer: Computer;
    let owned = false;
    let created = false;
    let keep = false;
    let revision: WorkspaceRevision | undefined;

    if (selected) {
      computer = await Computer.get(selected);
      const sameSavedComputer = saved?.computerId === computer.id;
      owned = sameSavedComputer ? saved.owned : false;
      keep = sameSavedComputer ? saved.keep : false;
      revision = sameSavedComputer ? saved.revision : undefined;
    } else if (saved) {
      const forkNeedsOwnComputer = event.reason === "fork" && saved.owned;
      if (forkNeedsOwnComputer) {
        computer = await Computer.create();
        owned = true;
        created = true;
      } else {
        let restored = true;
        try {
          computer = await Computer.get(saved.computerId);
        } catch (error) {
          if (!(error instanceof CloudApiError) || error.status !== 404)
            throw error;
          computer = await Computer.create();
          owned = true;
          created = true;
          restored = false;
        }
        if (["deleted", "deleting"].includes(computer.status)) {
          computer = await Computer.create();
          owned = true;
          created = true;
          restored = false;
        }
        if (restored) {
          owned = saved.owned;
          keep = saved.keep;
          revision = saved.revision;
        }
      }
    } else {
      computer = await Computer.create();
      owned = true;
      created = true;
    }

    let remoteWorkspace: string;
    try {
      await ensureComputerRunning(computer);
      remoteWorkspace = await prepareRemoteWorkspace(computer);
    } catch (error) {
      if (created) {
        try {
          await computer.delete();
        } catch {
          throw new Error(
            `${errorMessage(error)} Delete the unfinished computer with celesto computer delete ${computer.id} --cloud.`,
          );
        }
      }
      throw error;
    }
    const next: RuntimeState = {
      version: STATE_VERSION,
      computerId: computer.id,
      computerName: computer.name,
      owned,
      keep,
      localRoot: ctx.cwd,
      revision,
      computer,
      remoteWorkspace,
    };
    runtime = next;
    persist(next);
    updateStatus(ctx);

    if (event.reason !== "reload") {
      ctx.ui.notify(
        `Celesto computer "${computer.name}" is ready at ${REMOTE_WORKSPACE_DISPLAY}. No local files were copied. Run /celesto push to copy this project explicitly.`,
        "info",
      );
    }
    return next;
  }

  async function ensureRuntime(ctx?: ExtensionContext): Promise<RuntimeState> {
    if (runtime) return runtime;
    if (startupError) throw startupError;
    if (starting) return starting;
    if (!ctx) {
      throw new Error("Celesto is not connected. Run pi --celesto and retry.");
    }
    starting = initialize({ type: "session_start", reason: "startup" }, ctx)
      .then((state) => {
        if (!state) {
          throw new Error(
            "Celesto is disabled. Start Pi with --celesto and retry.",
          );
        }
        return state;
      })
      .catch((error) => {
        startupError =
          error instanceof Error ? error : new Error(errorMessage(error));
        throw startupError;
      })
      .finally(() => {
        starting = undefined;
      });
    return starting;
  }

  async function performSync(ctx: ExtensionContext): Promise<SyncResult> {
    const state = await ensureRuntime(ctx);
    if (!state.revision) {
      throw new Error(
        "This workspace has no shared revision. Run /celesto push before /celesto sync.",
      );
    }
    updateStatus(ctx, "syncing");
    try {
      const result = await syncWorkspace(
        state.computer,
        state.localRoot,
        state.remoteWorkspace,
        state.revision,
      );
      if (result.conflicts.length === 0) {
        state.revision = result.revision;
        persist(state);
      }
      return result;
    } finally {
      updateStatus(ctx);
    }
  }

  async function runWorkspaceOperation<T>(
    operation: () => Promise<T>,
  ): Promise<T> {
    if (workspaceOperation) {
      throw new Error("Another Celesto workspace transfer is already running.");
    }
    const current = operation();
    workspaceOperation = current;
    try {
      return await current;
    } finally {
      if (workspaceOperation === current) workspaceOperation = undefined;
    }
  }

  async function syncOnce(ctx: ExtensionContext): Promise<SyncResult> {
    if (!syncing) {
      syncing = runWorkspaceOperation(() => performSync(ctx)).finally(() => {
        syncing = undefined;
      });
    }
    return syncing;
  }

  pi.on("session_start", async (event, ctx) => {
    startupError = undefined;
    try {
      starting = initialize(event, ctx)
        .then((state) => {
          if (!state) throw new Error("Celesto is disabled.");
          return state;
        })
        .finally(() => {
          starting = undefined;
        });
      await starting;
    } catch (error) {
      ctx.ui.setStatus("celesto", undefined);
      if (errorMessage(error) !== "Celesto is disabled.") {
        startupError =
          error instanceof Error ? error : new Error(errorMessage(error));
        ctx.ui.notify(errorMessage(error), "error");
      }
    }
  });

  pi.on("session_shutdown", async (event, ctx) => {
    const state = runtime;
    if (!state || event.reason === "reload") return;

    if (state.owned && !state.keep) {
      ctx.ui.notify(
        `Celesto computer "${state.computerName}" will be deleted. Any unsynced changes will be lost.`,
        "warning",
      );
      try {
        updateStatus(ctx, "deleting");
        await state.computer.delete();
      } catch (error) {
        ctx.ui.notify(
          `Could not delete Celesto computer "${state.computerName}": ${errorMessage(error)} Delete it with celesto computer delete ${state.computerId} --cloud.`,
          "warning",
        );
      }
    }
    runtime = undefined;
    updateStatus(ctx);
  });

  pi.registerCommand("celesto", {
    description:
      "Manage the active Celesto computer: status, push, sync, or keep",
    handler: async (args, ctx) => {
      const action = args.trim() || "status";
      if (action === "status") {
        try {
          const state = await ensureRuntime(ctx);
          ctx.ui.notify(
            [
              `Computer: ${state.computerName} (${state.computerId})`,
              `Status: ${state.computer.status}`,
              `Workspace: ${REMOTE_WORKSPACE_DISPLAY} (${state.remoteWorkspace})`,
              `Cleanup: ${state.owned ? (state.keep ? "keep" : "delete on exit without syncing") : "caller-owned; never delete"}`,
              `Revision: ${state.revision?.id ?? "not synchronized"}`,
            ].join("\n"),
            "info",
          );
        } catch (error) {
          ctx.ui.notify(errorMessage(error), "error");
        }
        return;
      }

      if (action === "push") {
        try {
          const state = await ensureRuntime(ctx);
          if (state.revision) {
            throw new Error(
              "This workspace already has a shared revision. Run /celesto sync instead.",
            );
          }
          assertSafeLocalRoot(state.localRoot);
          await runWorkspaceOperation(async () => {
            updateStatus(ctx, "uploading");
            const uploaded = await uploadInitialWorkspace(
              state.computer,
              state.localRoot,
              state.remoteWorkspace,
            );
            state.revision = uploaded.revision;
            persist(state);
            const skipped =
              uploaded.scan.skippedLargeFiles + uploaded.scan.skippedSymlinks;
            ctx.ui.notify(
              `Copied this project to "${state.computerName}".${
                skipped > 0
                  ? ` Skipped ${skipped} unsafe or oversized files.`
                  : ""
              }`,
              "info",
            );
          });
        } catch (error) {
          ctx.ui.notify(`Celesto push failed: ${errorMessage(error)}`, "error");
        } finally {
          updateStatus(ctx);
        }
        return;
      }

      if (action === "sync") {
        try {
          const result = await syncOnce(ctx);
          if (result.conflicts.length > 0) {
            ctx.ui.notify(
              `Sync preserved ${result.conflicts.length} conflict(s) under .celesto-conflicts/${result.revision.id}. Resolve them, then run /celesto sync again.`,
              "warning",
            );
          } else {
            ctx.ui.notify(
              `Celesto sync complete: pulled ${result.pulled}, pushed ${result.pushed}.`,
              "info",
            );
          }
        } catch (error) {
          ctx.ui.notify(
            `Celesto sync failed: ${errorMessage(error)} Run /celesto sync to retry; the computer was kept.`,
            "error",
          );
        }
        return;
      }

      if (action === "keep") {
        try {
          const state = await ensureRuntime(ctx);
          state.keep = true;
          persist(state);
          ctx.ui.notify(
            `Celesto computer "${state.computerName}" will be kept after Pi exits. Delete it later with celesto computer delete ${state.computerId} --cloud.`,
            "info",
          );
        } catch (error) {
          ctx.ui.notify(errorMessage(error), "error");
        }
        return;
      }

      ctx.ui.notify(
        `Unknown Celesto action "${action}". Use /celesto status, /celesto push, /celesto sync, or /celesto keep.`,
        "error",
      );
    },
  });

  pi.registerTool({
    ...localRead,
    async execute(id, params, signal, onUpdate, ctx) {
      if (!modeEnabled) {
        return createReadTool(ctx.cwd).execute(id, params, signal, onUpdate);
      }
      const state = await ensureRuntime(ctx);
      return createReadTool(state.remoteWorkspace, {
        operations: createCelestoReadOperations(
          state.computer,
          state.localRoot,
          state.remoteWorkspace,
        ),
      }).execute(id, params, signal, onUpdate);
    },
  });

  pi.registerTool({
    ...localWrite,
    async execute(id, params, signal, onUpdate, ctx) {
      if (!modeEnabled) {
        return createWriteTool(ctx.cwd).execute(id, params, signal, onUpdate);
      }
      const state = await ensureRuntime(ctx);
      return createWriteTool(state.remoteWorkspace, {
        operations: createCelestoWriteOperations(
          state.computer,
          state.localRoot,
          state.remoteWorkspace,
        ),
      }).execute(id, params, signal, onUpdate);
    },
  });

  pi.registerTool({
    ...localEdit,
    async execute(id, params, signal, onUpdate, ctx) {
      if (!modeEnabled) {
        return createEditTool(ctx.cwd).execute(id, params, signal, onUpdate);
      }
      const state = await ensureRuntime(ctx);
      return createEditTool(state.remoteWorkspace, {
        operations: createCelestoEditOperations(
          state.computer,
          state.localRoot,
          state.remoteWorkspace,
        ),
      }).execute(id, params, signal, onUpdate);
    },
  });

  pi.registerTool({
    ...localBash,
    async execute(id, params, signal, onUpdate, ctx) {
      if (!modeEnabled) {
        return createBashTool(ctx.cwd).execute(id, params, signal, onUpdate);
      }
      const state = await ensureRuntime(ctx);
      return createBashTool(state.remoteWorkspace, {
        operations: createCelestoBashOperations(
          state.computer,
          state.localRoot,
          state.remoteWorkspace,
        ),
      }).execute(id, params, signal, onUpdate);
    },
  });

  pi.on("user_bash", async (_event, ctx) => {
    if (!modeEnabled) return undefined;
    const state = await ensureRuntime(ctx);
    return {
      operations: createCelestoBashOperations(
        state.computer,
        state.localRoot,
        state.remoteWorkspace,
      ),
    };
  });

  pi.on("before_agent_start", async (event) => {
    if (!runtime) return undefined;
    const currentDirectory = `Current working directory: ${runtime.localRoot}`;
    const remoteDirectory = `Current working directory: ${runtime.remoteWorkspace} (${REMOTE_WORKSPACE_DISPLAY} on Celesto computer: ${runtime.computerName})`;
    const localRoot = runtime.localRoot.replaceAll("\\", "/");
    const remoteWorkspace = runtime.remoteWorkspace;
    const cwdSection = new RegExp(
      `<cwd>\\s*${localRoot.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*</cwd>`,
      "g",
    );
    const systemPrompt = event.systemPrompt.replace(
      cwdSection,
      () => `<cwd>${remoteWorkspace}</cwd>`,
    );
    if (systemPrompt !== event.systemPrompt) return { systemPrompt };
    return {
      systemPrompt: event.systemPrompt.includes(currentDirectory)
        ? event.systemPrompt.replace(currentDirectory, () => remoteDirectory)
        : `${event.systemPrompt}\n\n${remoteDirectory}`,
    };
  });
}
