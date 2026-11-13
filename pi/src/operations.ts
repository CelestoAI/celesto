import { randomUUID } from "node:crypto";
import path from "node:path";

import type {
  BashOperations,
  EditOperations,
  ReadOperations,
  WriteOperations,
} from "@earendil-works/pi-coding-agent";
import type {
  ComputerExecResponse,
  ComputerExecStreamEvent,
  ExecParams,
} from "./computer.js";

export const REMOTE_WORKSPACE_DISPLAY = "$HOME/workspace";
const LEGACY_REMOTE_WORKSPACE = "/workspace";
const REMOTE_WRITE_CHUNK_CHARACTERS = 8_000;

export interface RemoteComputer {
  run(command: string, params?: ExecParams): Promise<ComputerExecResponse>;
  runStream(
    command: string,
    params?: ExecParams,
  ): AsyncGenerator<ComputerExecStreamEvent>;
}

export function shellQuote(value: string): string {
  return `'${value.replaceAll("'", `'"'"'`)}'`;
}

export function toRemotePath(
  inputPath: string,
  localRoot: string,
  remoteRoot: string,
): string {
  const normalizedRemoteRoot = path.posix.resolve(remoteRoot);
  const asPosix = inputPath.replaceAll("\\", "/");

  if (
    asPosix === normalizedRemoteRoot ||
    asPosix.startsWith(`${normalizedRemoteRoot}/`)
  ) {
    const normalized = path.posix.resolve(asPosix);
    if (
      normalized !== normalizedRemoteRoot &&
      !normalized.startsWith(`${normalizedRemoteRoot}/`)
    ) {
      throw new Error(`Path must stay inside ${remoteRoot}.`);
    }
    return normalized;
  }

  const absoluteLocalRoot = path.resolve(localRoot);
  const absoluteInput = path.isAbsolute(inputPath)
    ? path.resolve(inputPath)
    : path.resolve(absoluteLocalRoot, inputPath);
  const relative = path.relative(absoluteLocalRoot, absoluteInput);
  if (
    relative === ".." ||
    relative.startsWith(`..${path.sep}`) ||
    path.isAbsolute(relative)
  ) {
    throw new Error(`Path must stay inside ${localRoot}.`);
  }

  return relative
    ? path.posix.join(normalizedRemoteRoot, ...relative.split(path.sep))
    : normalizedRemoteRoot;
}

function commandError(action: string, response: ComputerExecResponse): Error {
  const detail = response.stderr.trim() || response.stdout.trim();
  return new Error(
    detail
      ? `${action} failed: ${detail}`
      : `${action} failed with exit code ${response.exitCode}.`,
  );
}

export async function execChecked(
  computer: RemoteComputer,
  command: string,
  action: string,
  params: ExecParams = {},
): Promise<ComputerExecResponse> {
  const response = await computer.run(command, params);
  if (response.exitCode !== 0) {
    throw commandError(action, response);
  }
  return response;
}

/** Prepare $HOME/workspace and migrate a non-empty legacy /workspace. */
export async function prepareRemoteWorkspace(
  computer: RemoteComputer,
  options: { legacyRoot?: string } = {},
): Promise<string> {
  const legacyRoot = options.legacyRoot ?? LEGACY_REMOTE_WORKSPACE;
  const response = await execChecked(
    computer,
    [
      "set -eu",
      'home=$(cd "${HOME:?HOME is not set}" && pwd -P)',
      'target="$home/workspace"',
      `legacy=${shellQuote(legacyRoot)}`,
      "target_has_files=false",
      'if [ -d "$target" ] && find "$target" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then target_has_files=true; fi',
      'if [ "$target_has_files" = false ] && [ -d "$legacy" ] && find "$legacy" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then rm -rf -- "$target"; mv "$legacy" "$target"; else mkdir -p "$target"; fi',
      'cd "$target"',
      "pwd -P",
    ].join("; "),
    `Prepare ${REMOTE_WORKSPACE_DISPLAY}`,
  );
  const remoteRoot = response.stdout.trim();
  if (!path.posix.isAbsolute(remoteRoot) || remoteRoot === "/") {
    throw new Error(
      `Celesto returned an invalid workspace path for ${REMOTE_WORKSPACE_DISPLAY}.`,
    );
  }
  return path.posix.resolve(remoteRoot);
}

export async function readRemoteFile(
  computer: RemoteComputer,
  remotePath: string,
): Promise<Buffer> {
  const response = await execChecked(
    computer,
    `base64 < ${shellQuote(remotePath)} | tr -d '\\n'`,
    `Read ${remotePath}`,
  );
  const encoded = response.stdout.trim();
  if (
    !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(
      encoded,
    )
  ) {
    throw new Error(`Celesto returned invalid file data for ${remotePath}.`);
  }
  return Buffer.from(encoded, "base64");
}

export async function writeRemoteFile(
  computer: RemoteComputer,
  remotePath: string,
  content: Buffer | string,
): Promise<void> {
  const encoded = Buffer.isBuffer(content)
    ? content.toString("base64")
    : Buffer.from(content).toString("base64");
  const parent = path.posix.dirname(remotePath);
  const transferId = randomUUID();
  const encodedPath = `${remotePath}.celesto.${transferId}.b64`;
  const temporaryPath = `${remotePath}.celesto.${transferId}.tmp`;

  try {
    await execChecked(
      computer,
      [
        "set -eu",
        `mkdir -p ${shellQuote(parent)}`,
        "umask 077",
        `: > ${shellQuote(encodedPath)}`,
        `: > ${shellQuote(temporaryPath)}`,
      ].join("; "),
      `Prepare ${remotePath}`,
    );
    for (
      let offset = 0;
      offset < encoded.length;
      offset += REMOTE_WRITE_CHUNK_CHARACTERS
    ) {
      const chunk = encoded.slice(
        offset,
        offset + REMOTE_WRITE_CHUNK_CHARACTERS,
      );
      await execChecked(
        computer,
        `printf %s ${shellQuote(chunk)} >> ${shellQuote(encodedPath)}`,
        `Write ${remotePath}`,
        { timeout: 300 },
      );
    }
    await execChecked(
      computer,
      [
        "set -eu",
        `base64 -d ${shellQuote(encodedPath)} > ${shellQuote(temporaryPath)}`,
        `rm -f -- ${shellQuote(encodedPath)}`,
        `mv ${shellQuote(temporaryPath)} ${shellQuote(remotePath)}`,
      ].join("; "),
      `Finish ${remotePath}`,
      { timeout: 300 },
    );
  } finally {
    await computer
      .run(`rm -f -- ${shellQuote(encodedPath)} ${shellQuote(temporaryPath)}`)
      .catch(() => undefined);
  }
}

export async function removeRemotePath(
  computer: RemoteComputer,
  remotePath: string,
): Promise<void> {
  await execChecked(
    computer,
    `rm -f -- ${shellQuote(remotePath)}`,
    `Delete ${remotePath}`,
  );
}

function imageMimeType(filePath: string): string | null {
  switch (path.extname(filePath).toLowerCase()) {
    case ".jpg":
    case ".jpeg":
      return "image/jpeg";
    case ".png":
      return "image/png";
    case ".gif":
      return "image/gif";
    case ".webp":
      return "image/webp";
    default:
      return null;
  }
}

export function createCelestoReadOperations(
  computer: RemoteComputer,
  localRoot: string,
  remoteRoot: string,
): ReadOperations {
  const remote = (input: string) => toRemotePath(input, localRoot, remoteRoot);
  return {
    readFile: (input) => readRemoteFile(computer, remote(input)),
    access: async (input) => {
      const remotePath = remote(input);
      await execChecked(
        computer,
        `test -r ${shellQuote(remotePath)}`,
        `Open ${remotePath}`,
      );
    },
    detectImageMimeType: async (input) => imageMimeType(remote(input)),
  };
}

export function createCelestoWriteOperations(
  computer: RemoteComputer,
  localRoot: string,
  remoteRoot: string,
): WriteOperations {
  const remote = (input: string) => toRemotePath(input, localRoot, remoteRoot);
  return {
    writeFile: (input, content) =>
      writeRemoteFile(computer, remote(input), content),
    mkdir: async (input) => {
      const remotePath = remote(input);
      await execChecked(
        computer,
        `mkdir -p ${shellQuote(remotePath)}`,
        `Create ${remotePath}`,
      );
    },
  };
}

export function createCelestoEditOperations(
  computer: RemoteComputer,
  localRoot: string,
  remoteRoot: string,
): EditOperations {
  const read = createCelestoReadOperations(computer, localRoot, remoteRoot);
  const write = createCelestoWriteOperations(computer, localRoot, remoteRoot);
  const remote = (input: string) => toRemotePath(input, localRoot, remoteRoot);
  return {
    readFile: read.readFile,
    writeFile: write.writeFile,
    access: async (input) => {
      const remotePath = remote(input);
      await execChecked(
        computer,
        `test -r ${shellQuote(remotePath)} && test -w ${shellQuote(remotePath)}`,
        `Edit ${remotePath}`,
      );
    },
  };
}

async function terminateRemoteCommand(
  computer: RemoteComputer,
  pidFile: string,
): Promise<void> {
  const command = [
    "attempt=0",
    'while [ "$attempt" -lt 20 ]; do',
    `  if [ -r ${shellQuote(pidFile)} ]; then`,
    `    pid=$(cat ${shellQuote(pidFile)})`,
    "    case \"$pid\" in ''|*[!0-9]*) exit 0 ;; esac",
    "    pgid=$(ps -o pgid= -p \"$pid\" 2>/dev/null | tr -d ' ')",
    '    if [ "$pgid" = "$pid" ]; then',
    '      /bin/kill -TERM -- "-$pid" 2>/dev/null || true',
    "      sleep 0.2",
    '      /bin/kill -KILL -- "-$pid" 2>/dev/null || true',
    "    fi",
    `    rm -f -- ${shellQuote(pidFile)}`,
    "    exit 0",
    "  fi",
    "  attempt=$((attempt + 1))",
    "  sleep 0.05",
    "done",
  ].join("\n");
  await computer.run(command, { timeout: 10 });
}

export function createCelestoBashOperations(
  computer: RemoteComputer,
  localRoot: string,
  remoteRoot: string,
): BashOperations {
  return {
    exec: async (command, cwd, { onData, signal, timeout }) => {
      const remoteCwd = toRemotePath(cwd, localRoot, remoteRoot);
      const timeoutSeconds =
        timeout === undefined ? undefined : Math.max(1, Math.min(300, timeout));
      const token = randomUUID();
      const pidFile = `/tmp/celesto-pi-${token}.pid`;
      const childCommand = `env CELESTO_PI_COMMAND_ID=${shellQuote(token)} setsid sh -c ${shellQuote(command)}`;
      const commandBody = [
        `${childCommand} & child=$!`,
        `printf '%s\\n' \"$child\" > ${shellQuote(pidFile)}`,
        'wait "$child"',
        "status=$?",
        `rm -f -- ${shellQuote(pidFile)}`,
        'exit "$status"',
      ].join("; ");
      const remoteCommand = `cd ${shellQuote(remoteCwd)} && { ${commandBody}; }`;
      let exitCode: number | null = null;
      let cleanupPromise: Promise<void> | undefined;
      const cleanup = (): Promise<void> => {
        cleanupPromise ??= terminateRemoteCommand(computer, pidFile).catch(
          () => undefined,
        );
        return cleanupPromise;
      };
      const onAbort = (): void => {
        void cleanup();
      };
      signal?.addEventListener("abort", onAbort, { once: true });

      try {
        for await (const event of computer.runStream(remoteCommand, {
          signal,
          timeout: timeoutSeconds,
        })) {
          if (event.type === "stdout" || event.type === "stderr") {
            onData(Buffer.from(event.data));
          } else if (event.type === "exit") {
            exitCode = event.exitCode;
          }
        }
      } catch (error) {
        await cleanup();
        if (signal?.aborted) {
          throw new Error("aborted");
        }
        throw error;
      } finally {
        signal?.removeEventListener("abort", onAbort);
      }

      if (signal?.aborted) {
        await cleanup();
        throw new Error("aborted");
      }
      return { exitCode };
    },
  };
}
