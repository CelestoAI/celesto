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

export interface RemoteFileGuard {
  expected?: { sha256: string; size: number; mode: number };
  mode?: number;
  root?: string;
}

export function shellQuote(value: string): string {
  return `'${value.replaceAll("'", `'"'"'`)}'`;
}

function checkedRemoteParents(root: string): string[] {
  return [
    [
      `celesto_checked_root=${shellQuote(root)}`,
      "celesto_parent_changed() { printf '%s\\n' 'Workspace changed during sync; retry /celesto sync.' >&2; exit 1; }",
      'case "$celesto_target" in "$celesto_checked_root"/*) ;; *) celesto_parent_changed ;; esac',
      'celesto_checked_parent="${celesto_target%/*}"; if [ -z "$celesto_checked_parent" ]; then celesto_checked_parent=/; fi',
      "while :; do",
      '  if [ -L "$celesto_checked_parent" ]; then celesto_parent_changed; fi',
      '  if [ "$celesto_checked_parent" = "$celesto_checked_root" ]; then break; fi',
      '  if [ "$celesto_checked_parent" = / ]; then celesto_parent_changed; fi',
      '  celesto_checked_parent="${celesto_checked_parent%/*}"; if [ -z "$celesto_checked_parent" ]; then celesto_checked_parent=/; fi',
      "done",
    ].join("\n"),
  ];
}

function guardedRemoteCommit(
  guard: RemoteFileGuard,
  install: boolean,
): string[] {
  const target = '"$celesto_target"';
  const previous = '"$celesto_previous"';
  const changed = "Workspace changed during sync; retry /celesto sync.";
  const commands = [
    "celesto_claimed=false",
    "celesto_changed() {",
    `  if [ "$celesto_claimed" = true ] && { [ -e ${previous} ] || [ -L ${previous} ]; }; then`,
    `    mv -T -n -- ${previous} ${target} 2>/dev/null || true`,
    `    if [ -e ${previous} ] || [ -L ${previous} ]; then`,
    `      printf '%s Previous destination retained at %s\\n' ${shellQuote(changed)} ${previous} >&2; exit 1`,
    "    fi",
    "  fi",
    `  printf '%s\\n' ${shellQuote(changed)} >&2; exit 1`,
    "}",
  ];
  if (guard.root) commands.push(...checkedRemoteParents(guard.root));
  if (guard.expected) {
    const expected = guard.expected;
    commands.push(
      `if ! mv -T -- ${target} ${previous}; then celesto_changed; fi`,
      "celesto_claimed=true",
      `if [ -L ${previous} ] || [ ! -f ${previous} ] || [ "$(stat -c '%s' -- ${previous})" != ${shellQuote(String(expected.size))} ] || [ "$((0$(stat -c '%a' -- ${previous}) & 0777))" -ne ${expected.mode} ] || [ "$(sha256sum < ${previous} | cut -d ' ' -f 1)" != ${shellQuote(expected.sha256)} ]; then celesto_changed; fi`,
    );
  } else {
    commands.push(
      `if [ -d ${target} ] && [ ! -L ${target} ]; then`,
      `  if ! mv -T -- ${target} ${previous}; then celesto_changed; fi`,
      "  celesto_claimed=true",
      `  if [ -L ${previous} ] || [ ! -d ${previous} ] || ! rmdir -- ${previous}; then celesto_changed; fi`,
      `elif [ -e ${target} ] || [ -L ${target} ]; then celesto_changed; fi`,
    );
  }
  if (install)
    commands.push(
      `if ! ln -T -- "$celesto_staged" ${target}; then celesto_changed; fi`,
    );
  commands.push(`rm -f -- ${previous}`);
  return [commands.join("\n")];
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
    `base64 < ${shellQuote(remotePath)}`,
    `Read ${remotePath}`,
  );
  const encoded = response.stdout.trim().replace(/\r?\n/g, "");
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
  guard?: RemoteFileGuard,
): Promise<void> {
  const encoded = Buffer.isBuffer(content)
    ? content.toString("base64")
    : Buffer.from(content).toString("base64");
  const parent = path.posix.dirname(remotePath);
  const transferId = randomUUID();
  // Bind the path once per request; derive sibling paths without repeating a
  // potentially long, shell-escaped destination in each command.
  const prefix = [
    "set -eu",
    `celesto_target=${shellQuote(remotePath)}`,
    `celesto_encoded="$celesto_target.celesto.${transferId}.b64"`,
    `celesto_staged="$celesto_target.celesto.${transferId}.tmp"`,
    `celesto_previous="$celesto_target.celesto-sync-backup.${transferId}"`,
    ...(guard?.root ? checkedRemoteParents(guard.root) : []),
  ];
  const uploadCommand = (chunk: string): string =>
    [...prefix, `printf %s ${shellQuote(chunk)} >> "$celesto_encoded"`].join(
      "; ",
    );
  // Base64 contains no shell quotes, so its length adds directly to the
  // complete command overhead, including escaped paths and parent checks.
  const chunkCharacters = Math.min(
    REMOTE_WRITE_CHUNK_CHARACTERS,
    10_000 - uploadCommand("").length,
  );
  if (chunkCharacters < 1)
    throw new Error(
      "Cloud cannot upload this path within its command limit. Shorten the file path and retry.",
    );

  try {
    await execChecked(
      computer,
      [
        ...prefix,
        `mkdir -p ${shellQuote(parent)}`,
        "umask 077",
        ': > "$celesto_encoded"',
        ': > "$celesto_staged"',
      ].join("; "),
      `Prepare ${remotePath}`,
    );
    for (let offset = 0; offset < encoded.length; offset += chunkCharacters) {
      const chunk = encoded.slice(offset, offset + chunkCharacters);
      await execChecked(computer, uploadCommand(chunk), `Write ${remotePath}`, {
        timeout: 300,
      });
    }
    await execChecked(
      computer,
      [
        ...prefix,
        'base64 -d "$celesto_encoded" > "$celesto_staged"',
        'rm -f -- "$celesto_encoded"',
        ...(guard
          ? [
              `chmod ${(guard.mode ?? guard.expected?.mode ?? 0o600).toString(8)} "$celesto_staged"`,
              ...guardedRemoteCommit(guard, true),
            ]
          : [
              `if [ -f "$celesto_target" ]; then celesto_mode=$(stat -c '%a' "$celesto_target"); chmod "$(printf '%o' "$((0$celesto_mode & 0777))")" "$celesto_staged"; fi`,
              'mv -T "$celesto_staged" "$celesto_target"',
            ]),
      ].join("; "),
      `Finish ${remotePath}`,
      { timeout: 300 },
    );
  } finally {
    await computer
      .run(
        [...prefix, 'rm -f -- "$celesto_encoded" "$celesto_staged"'].join("; "),
      )
      .catch(() => undefined);
  }
}

export async function removeRemotePath(
  computer: RemoteComputer,
  remotePath: string,
  remoteRoot: string,
  guard?: RemoteFileGuard,
): Promise<void> {
  if (!remotePath.startsWith(`${remoteRoot}/`))
    throw new Error("Sync paths must stay inside the remote workspace.");
  await execChecked(
    computer,
    [
      "set -eu",
      ...(guard
        ? [
            `celesto_target=${shellQuote(remotePath)}`,
            `celesto_previous="$celesto_target.celesto-sync-backup.${randomUUID()}"`,
            ...guardedRemoteCommit(guard, false),
          ]
        : [`rm -f -- ${shellQuote(remotePath)}`]),
      `parent=${shellQuote(path.posix.dirname(remotePath))}`,
      `while [ "$parent" != ${shellQuote(remoteRoot)} ]; do rmdir -- "$parent" 2>/dev/null || break; parent="\${parent%/*}"; if [ -z "$parent" ]; then parent=/; fi; done`,
    ].join("; "),
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
        timeout === undefined
          ? undefined
          : Math.max(1, Math.min(300, Math.ceil(timeout)));
      const token = randomUUID();
      const pidFile = `/tmp/celesto-pi-${token}.pid`;
      const childCommand = `env CELESTO_PI_COMMAND_ID=${shellQuote(token)} setsid bash --noprofile --norc -c ${shellQuote(command)}`;
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
            if (event.timedOut) await cleanup();
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
