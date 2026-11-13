import { createHash, randomUUID } from "node:crypto";
import {
  chmod,
  copyFile,
  lstat,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  rename,
  rmdir,
  rm,
  stat,
  writeFile,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import createIgnore, { type Ignore } from "ignore";
import * as tar from "tar";

import {
  execChecked,
  removeRemotePath,
  shellQuote,
  type RemoteComputer,
  writeRemoteFile,
} from "./operations.js";

export const REVISION_FILE = ".celesto-sync.json";
export const DEFAULT_MAX_FILE_BYTES = 25 * 1024 * 1024;
const ARCHIVE_CHUNK_CHARACTERS = 8_000;

const SAFE_IGNORE_PATTERNS = [
  REVISION_FILE,
  ".celesto-conflicts/",
  "**/.celesto-conflicts/",
  ".env",
  ".env.*",
  "!.env.example",
  "**/*.pem",
  "**/*.key",
  "**/*.p12",
  "**/*.pfx",
  "**/credentials.json",
  "**/.netrc",
  "**/.npmrc",
  "**/.pypirc",
  "**/.git-credentials",
  "**/id_rsa",
  "**/id_ed25519",
  "**/.pi/agent/auth.json",
  "**/.docker/config.json",
  ".aws/",
  "**/.aws/",
  ".azure/",
  "**/.azure/",
  ".config/gcloud/",
  "**/.config/gcloud/",
  ".kube/",
  "**/.kube/",
  ".ssh/",
  "**/.ssh/",
  "node_modules/",
  "**/node_modules/",
  "dist/",
  "**/dist/",
  "build/",
  "**/build/",
  "coverage/",
  "**/coverage/",
  ".next/",
  "**/.next/",
];

export interface WorkspaceFile {
  sha256: string;
  size: number;
  mode: number;
}

export type WorkspaceManifest = Record<string, WorkspaceFile>;

export interface WorkspaceRevision {
  version: 1;
  id: string;
  files: WorkspaceManifest;
}

export interface WorkspaceScan {
  files: string[];
  manifest: WorkspaceManifest;
  skippedSymlinks: number;
  skippedLargeFiles: number;
  excludedPaths: string[];
}

export interface SyncResult {
  revision: WorkspaceRevision;
  conflicts: string[];
  pulled: number;
  pushed: number;
}

export interface WorkspaceSyncPlan {
  pull: string[];
  push: string[];
  conflicts: string[];
}

export interface RemoteSnapshot {
  root: string;
  excludedPaths: string[];
  cleanup(): Promise<void>;
}

async function readPatterns(root: string, name: string): Promise<string> {
  try {
    return await readFile(path.join(root, name), "utf8");
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return "";
    throw error;
  }
}

/** Celesto-specific patterns take precedence over .gitignore patterns. */
export async function createWorkspaceIgnore(root: string): Promise<Ignore> {
  const [celestoPatterns, gitPatterns] = await Promise.all([
    readPatterns(root, ".celestoignore"),
    readPatterns(root, ".gitignore"),
  ]);
  return createIgnore()
    .add(SAFE_IGNORE_PATTERNS)
    .add(gitPatterns)
    .add(celestoPatterns);
}

function portablePath(value: string): string {
  return value.split(path.sep).join("/");
}

async function hashFile(filePath: string): Promise<string> {
  const content = await readFile(filePath);
  return createHash("sha256").update(content).digest("hex");
}

export async function scanWorkspace(
  root: string,
  options: { ignore?: Ignore; maxFileBytes?: number } = {},
): Promise<WorkspaceScan> {
  const absoluteRoot = path.resolve(root);
  const matcher = options.ignore ?? (await createWorkspaceIgnore(absoluteRoot));
  const maxFileBytes = options.maxFileBytes ?? DEFAULT_MAX_FILE_BYTES;
  const files: string[] = [];
  const manifest: WorkspaceManifest = {};
  const excludedPaths: string[] = [];
  let skippedSymlinks = 0;
  let skippedLargeFiles = 0;

  async function walk(relativeDirectory: string): Promise<void> {
    const directory = path.join(absoluteRoot, relativeDirectory);
    const entries = await readdir(directory, { withFileTypes: true });
    entries.sort((a, b) => a.name.localeCompare(b.name));

    for (const entry of entries) {
      const relative = path.join(relativeDirectory, entry.name);
      const portable = portablePath(relative);
      const ignoredPath = entry.isDirectory() ? `${portable}/` : portable;
      if (matcher.ignores(ignoredPath)) {
        excludedPaths.push(portable);
        continue;
      }

      const absolute = path.join(absoluteRoot, relative);
      if (entry.isSymbolicLink()) {
        excludedPaths.push(portable);
        skippedSymlinks += 1;
        continue;
      }
      if (entry.isDirectory()) {
        await walk(relative);
        continue;
      }
      if (!entry.isFile()) {
        excludedPaths.push(portable);
        continue;
      }

      const info = await stat(absolute);
      if (info.size > maxFileBytes) {
        excludedPaths.push(portable);
        skippedLargeFiles += 1;
        continue;
      }
      files.push(portable);
      manifest[portable] = {
        sha256: await hashFile(absolute),
        size: info.size,
        mode: info.mode & 0o777,
      };
    }
  }

  await walk("");
  return { files, manifest, skippedSymlinks, skippedLargeFiles, excludedPaths };
}

function stableManifestJson(manifest: WorkspaceManifest): string {
  const sorted = Object.fromEntries(
    Object.entries(manifest).sort(([left], [right]) =>
      left.localeCompare(right),
    ),
  );
  return JSON.stringify(sorted);
}

export function createRevision(manifest: WorkspaceManifest): WorkspaceRevision {
  const id = createHash("sha256")
    .update(stableManifestJson(manifest))
    .digest("hex")
    .slice(0, 16);
  return { version: 1, id, files: manifest };
}

async function createArchive(root: string, files: string[]): Promise<string> {
  const directory = await mkdtemp(path.join(os.tmpdir(), "celesto-upload-"));
  const archivePath = path.join(directory, "workspace.tgz");
  await tar.create(
    {
      cwd: root,
      file: archivePath,
      gzip: true,
      portable: false,
      noMtime: true,
      follow: false,
    },
    files,
  );
  return archivePath;
}

async function uploadEncodedFile(
  computer: RemoteComputer,
  encoded: string,
  remotePath: string,
): Promise<void> {
  await execChecked(
    computer,
    `rm -f -- ${shellQuote(remotePath)} && : > ${shellQuote(remotePath)}`,
    "Prepare workspace upload",
  );
  for (
    let offset = 0;
    offset < encoded.length;
    offset += ARCHIVE_CHUNK_CHARACTERS
  ) {
    const chunk = encoded.slice(offset, offset + ARCHIVE_CHUNK_CHARACTERS);
    await execChecked(
      computer,
      `printf %s ${shellQuote(chunk)} >> ${shellQuote(remotePath)}`,
      "Upload workspace",
      { timeout: 300 },
    );
  }
}

export async function uploadInitialWorkspace(
  computer: RemoteComputer,
  localRoot: string,
  remoteRoot: string,
): Promise<{ revision: WorkspaceRevision; scan: WorkspaceScan }> {
  const ignore = await createWorkspaceIgnore(localRoot);
  const scan = await scanWorkspace(localRoot, { ignore });
  const archivePath =
    scan.files.length > 0
      ? await createArchive(localRoot, scan.files)
      : undefined;
  const temporaryId = randomUUID();
  const encodedRemote = `/tmp/celesto-${temporaryId}.b64`;
  const archiveRemote = `/tmp/celesto-${temporaryId}.tgz`;
  const staging = `${remoteRoot}.celesto-staging-${temporaryId}`;
  const backup = `${remoteRoot}.celesto-backup-${temporaryId}`;

  try {
    if (archivePath) {
      const encoded = (await readFile(archivePath)).toString("base64");
      await uploadEncodedFile(computer, encoded, encodedRemote);
    }
    const archiveCommands = archivePath
      ? [
          `base64 -d ${shellQuote(encodedRemote)} > ${shellQuote(archiveRemote)}`,
          `tar --no-same-owner -xpzf ${shellQuote(archiveRemote)} -C ${shellQuote(staging)}`,
          `rm -f -- ${shellQuote(encodedRemote)} ${shellQuote(archiveRemote)}`,
        ]
      : [];
    const command = [
      "set -eu",
      `rm -rf -- ${shellQuote(staging)} ${shellQuote(backup)}`,
      `mkdir -p ${shellQuote(staging)}`,
      ...archiveCommands,
      `if [ -e ${shellQuote(remoteRoot)} ]; then mv ${shellQuote(remoteRoot)} ${shellQuote(backup)}; fi`,
      `if mv ${shellQuote(staging)} ${shellQuote(remoteRoot)}; then rm -rf -- ${shellQuote(backup)}; else if [ -e ${shellQuote(backup)} ]; then mv ${shellQuote(backup)} ${shellQuote(remoteRoot)}; fi; exit 1; fi`,
    ].join("; ");
    await execChecked(computer, command, `Prepare ${remoteRoot}`, {
      timeout: 300,
    });

    const revision = createRevision(scan.manifest);
    await writeRemoteRevision(computer, remoteRoot, revision);
    return { revision, scan };
  } finally {
    if (archivePath) {
      await rm(path.dirname(archivePath), { recursive: true, force: true });
    }
    await computer
      .run(
        `rm -rf -- ${shellQuote(encodedRemote)} ${shellQuote(archiveRemote)} ${shellQuote(staging)}`,
      )
      .catch(() => undefined);
  }
}

export async function remoteWorkspaceHasFiles(
  computer: RemoteComputer,
  remoteRoot: string,
): Promise<boolean> {
  const result = await computer.run(
    `test -d ${shellQuote(remoteRoot)} && find ${shellQuote(remoteRoot)} -mindepth 1 -maxdepth 1 -print -quit | grep -q .`,
  );
  return result.exitCode === 0;
}

async function streamStdout(
  computer: RemoteComputer,
  command: string,
  action: string,
): Promise<Buffer> {
  const chunks: Buffer[] = [];
  let stderr = "";
  let exitCode: number | undefined;
  for await (const event of computer.runStream(command, { timeout: 300 })) {
    if (event.type === "stdout") chunks.push(Buffer.from(event.data));
    else if (event.type === "stderr") stderr += event.data;
    else if (event.type === "exit") exitCode = event.exitCode;
  }
  if (exitCode !== 0) {
    throw new Error(
      stderr.trim()
        ? `${action} failed: ${stderr.trim()}`
        : `${action} failed with exit code ${exitCode ?? "unknown"}.`,
    );
  }
  return Buffer.concat(chunks);
}

function safeArchivePath(entryPath: string): boolean {
  if (path.posix.isAbsolute(entryPath)) return false;
  return !entryPath.split("/").includes("..");
}

export async function downloadRemoteWorkspace(
  computer: RemoteComputer,
  remoteRoot: string,
): Promise<RemoteSnapshot> {
  const encoded = await streamStdout(
    computer,
    `bash --noprofile --norc -o pipefail -c ${shellQuote(`tar -czf - -C ${shellQuote(remoteRoot)} . | base64`)}`,
    `Download ${remoteRoot}`,
  );
  const directory = await mkdtemp(path.join(os.tmpdir(), "celesto-download-"));
  const archivePath = path.join(directory, "workspace.tgz");
  const root = path.join(directory, "workspace");
  await mkdir(root, { recursive: true });

  const excludedPaths: string[] = [];
  const fileModes = new Map<string, number>();
  let unsafePath = false;
  try {
    await writeFile(archivePath, Buffer.from(encoded.toString(), "base64"));
    await tar.extract({
      cwd: root,
      file: archivePath,
      preservePaths: false,
      strict: true,
      chmod: true,
      processUmask: 0,
      filter: (entryPath, entry) => {
        const entryType = "type" in entry ? entry.type : undefined;
        if (!safeArchivePath(entryPath)) {
          unsafePath = true;
          return false;
        }
        if (
          entryType !== "File" &&
          entryType !== "OldFile" &&
          entryType !== "ContiguousFile" &&
          entryType !== "Directory" &&
          entryType !== "GNUDumpDir"
        ) {
          excludedPaths.push(entryPath.replace(/^\.\//, "").replace(/\/$/, ""));
          return false;
        }
        if (
          entryType === "File" ||
          entryType === "OldFile" ||
          entryType === "ContiguousFile"
        ) {
          if (typeof entry.mode !== "number") {
            unsafePath = true;
            return false;
          }
          fileModes.set(entryPath, entry.mode & 0o777);
        }
        return true;
      },
    });
    if (unsafePath)
      throw new Error(
        "Celesto returned an invalid workspace archive. Retry /celesto sync.",
      );
    // Freshly created files still inherit the host umask. Restore the ordinary
    // archive permissions explicitly rather than recording masked metadata.
    for (const [name, mode] of fileModes)
      await chmod(await checkedLocalPath(root, name), mode);
  } catch (error) {
    await rm(directory, { recursive: true, force: true });
    throw error;
  }

  return {
    root,
    excludedPaths,
    cleanup: () => rm(directory, { recursive: true, force: true }),
  };
}

function sameFile(
  left: WorkspaceFile | undefined,
  right: WorkspaceFile | undefined,
): boolean {
  return (
    left?.sha256 === right?.sha256 &&
    left?.mode === right?.mode &&
    left?.size === right?.size
  );
}

export function planWorkspaceSync(
  base: WorkspaceManifest,
  local: WorkspaceManifest,
  remote: WorkspaceManifest,
): WorkspaceSyncPlan {
  const paths = new Set([
    ...Object.keys(base),
    ...Object.keys(local),
    ...Object.keys(remote),
  ]);
  const plan: WorkspaceSyncPlan = { pull: [], push: [], conflicts: [] };

  for (const relativePath of [...paths].sort()) {
    const baseFile = base[relativePath];
    const localFile = local[relativePath];
    const remoteFile = remote[relativePath];
    if (sameFile(localFile, remoteFile)) continue;

    const localUnchanged = sameFile(localFile, baseFile);
    const remoteUnchanged = sameFile(remoteFile, baseFile);
    if (localUnchanged && !remoteUnchanged) plan.pull.push(relativePath);
    else if (!localUnchanged && remoteUnchanged) plan.push.push(relativePath);
    else plan.conflicts.push(relativePath);
  }

  // A merge must be representable as a file tree on both sides. Conflicting
  // parent/child shapes keep the entire affected subtree out of mutations.
  const projectedLocal = new Map(Object.entries(local));
  const projectedRemote = new Map(Object.entries(remote));
  for (const name of plan.pull) {
    if (Object.hasOwn(remote, name)) projectedLocal.set(name, remote[name]!);
    else projectedLocal.delete(name);
  }
  for (const name of plan.push) {
    if (Object.hasOwn(local, name)) projectedRemote.set(name, local[name]!);
    else projectedRemote.delete(name);
  }
  const blockedRoots = new Set<string>();
  for (const tree of [projectedLocal, projectedRemote]) {
    for (const name of tree.keys()) {
      let parent = path.posix.dirname(name);
      while (parent !== ".") {
        if (tree.has(parent)) blockedRoots.add(parent);
        parent = path.posix.dirname(parent);
      }
    }
  }
  for (const name of paths) {
    if (
      [...blockedRoots].some(
        (root) => name === root || name.startsWith(`${root}/`),
      )
    ) {
      if (!plan.conflicts.includes(name)) plan.conflicts.push(name);
    }
  }
  const conflicts = new Set(plan.conflicts);
  plan.pull = plan.pull.filter((name) => !conflicts.has(name));
  plan.push = plan.push.filter((name) => !conflicts.has(name));
  return plan;
}

async function checkedLocalPath(
  localRoot: string,
  relativePath: string,
): Promise<string> {
  const root = path.resolve(localRoot);
  const destination = path.resolve(root, relativePath);
  const relative = path.relative(root, destination);
  if (
    relative === ".." ||
    relative.startsWith(`..${path.sep}`) ||
    path.isAbsolute(relative)
  ) {
    throw new Error("Sync paths must stay inside the local project.");
  }
  let current = root;
  for (const part of relative.split(path.sep)) {
    current = path.join(current, part);
    try {
      if ((await lstat(current)).isSymbolicLink())
        throw new Error(`Sync refuses a local symlink: ${current}`);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
  }
  return destination;
}

async function replaceLocalFile(
  destination: string,
  source: string,
  mode: number,
): Promise<void> {
  try {
    if ((await lstat(destination)).isDirectory()) await rmdir(destination);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  }
  await mkdir(path.dirname(destination), { recursive: true });
  const temporary = `${destination}.celesto.${randomUUID()}`;
  await copyFile(source, temporary);
  await chmod(temporary, mode);
  await rename(temporary, destination);
}

async function applyRemoteToLocal(
  localRoot: string,
  snapshotRoot: string,
  relativePath: string,
  remoteFile: WorkspaceFile | undefined,
): Promise<void> {
  const localPath = await checkedLocalPath(localRoot, relativePath);
  if (!remoteFile) {
    await rm(localPath, { force: true });
    let parent = path.dirname(localPath);
    while (parent !== path.resolve(localRoot)) {
      try {
        await rmdir(parent);
      } catch (error) {
        if (
          ["ENOTEMPTY", "EEXIST", "ENOENT"].includes(
            (error as NodeJS.ErrnoException).code ?? "",
          )
        )
          break;
        throw error;
      }
      parent = path.dirname(parent);
    }
    return;
  }
  await replaceLocalFile(
    localPath,
    path.join(snapshotRoot, relativePath),
    remoteFile.mode,
  );
}

async function pushLocalToRemote(
  computer: RemoteComputer,
  localRoot: string,
  remoteRoot: string,
  relativePath: string,
  localFile: WorkspaceFile | undefined,
): Promise<WorkspaceFile | undefined> {
  const remotePath = path.posix.join(remoteRoot, relativePath);
  if (!localFile) {
    await removeRemotePath(computer, remotePath, remoteRoot);
    return undefined;
  }
  const content = await readFile(
    await checkedLocalPath(localRoot, relativePath),
  );
  if (content.length > DEFAULT_MAX_FILE_BYTES)
    throw new Error(
      `${relativePath} grew past the transfer limit during sync. Retry /celesto sync.`,
    );
  await execChecked(
    computer,
    `if [ -d ${shellQuote(remotePath)} ]; then rmdir -- ${shellQuote(remotePath)}; fi`,
    `Replace ${remotePath}`,
  );
  await writeRemoteFile(computer, remotePath, content);
  await execChecked(
    computer,
    `chmod ${localFile.mode.toString(8)} ${shellQuote(remotePath)}`,
    `Update ${remotePath}`,
  );
  return {
    sha256: createHash("sha256").update(content).digest("hex"),
    size: content.length,
    mode: localFile.mode,
  };
}

async function preserveConflict(
  localRoot: string,
  snapshotRoot: string,
  revisionId: string,
  relativePath: string,
  remoteFile: WorkspaceFile | undefined,
): Promise<void> {
  const conflictPath = await checkedLocalPath(
    localRoot,
    path.join(
      ".celesto-conflicts",
      revisionId,
      `${relativePath}${remoteFile ? ".remote" : ".remote-deleted"}`,
    ),
  );
  await mkdir(path.dirname(conflictPath), { recursive: true });
  if (remoteFile) {
    await copyFile(path.join(snapshotRoot, relativePath), conflictPath);
  } else {
    await writeFile(
      conflictPath,
      "The file was deleted in the Celesto workspace.\n",
    );
  }
}

export async function writeRemoteRevision(
  computer: RemoteComputer,
  remoteRoot: string,
  revision: WorkspaceRevision,
): Promise<void> {
  await writeRemoteFile(
    computer,
    path.posix.join(remoteRoot, REVISION_FILE),
    `${JSON.stringify(revision)}\n`,
  );
}

export async function syncWorkspace(
  computer: RemoteComputer,
  localRoot: string,
  remoteRoot: string,
  baseRevision: WorkspaceRevision,
): Promise<SyncResult> {
  const ignore = await createWorkspaceIgnore(localRoot);
  const snapshot = await downloadRemoteWorkspace(computer, remoteRoot);

  try {
    const [localScan, remoteScan] = await Promise.all([
      scanWorkspace(localRoot, { ignore }),
      scanWorkspace(snapshot.root, { ignore }),
    ]);
    // A local link that collides with a remote file remains an explicit refusal,
    // even though other excluded paths are left untouched by the planner.
    for (const name of localScan.excludedPaths) {
      if (
        !remoteScan.files.some(
          (remoteName) =>
            remoteName === name || remoteName.startsWith(`${name}/`),
        )
      )
        continue;
      try {
        if ((await lstat(path.join(localRoot, name))).isSymbolicLink())
          throw new Error(
            `Sync refuses a local symlink: ${path.join(localRoot, name)}`,
          );
      } catch (error) {
        if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
      }
    }
    const excludedRoots = new Set([
      ...localScan.excludedPaths,
      ...remoteScan.excludedPaths,
      ...snapshot.excludedPaths,
    ]);
    // A skipped descendant also blocks replacing an ancestor file/directory.
    for (const name of [...excludedRoots]) {
      let parent = path.posix.dirname(name);
      while (parent !== ".") {
        if (
          [baseRevision.files, localScan.manifest, remoteScan.manifest].some(
            (files) => Object.hasOwn(files, parent),
          )
        )
          excludedRoots.add(parent);
        parent = path.posix.dirname(parent);
      }
    }
    const excluded = (name: string) =>
      [...excludedRoots].some(
        (root) => name === root || name.startsWith(`${root}/`),
      );
    const eligible = (files: WorkspaceManifest) =>
      Object.fromEntries(
        Object.entries(files).filter(([name]) => !excluded(name)),
      );
    const localFiles = eligible(localScan.manifest);
    const remoteFiles = eligible(remoteScan.manifest);
    const plan = planWorkspaceSync(
      eligible(baseRevision.files),
      localFiles,
      remoteFiles,
    );
    const shared = new Map(Object.entries(localFiles));
    const ordered = (names: string[], files: WorkspaceManifest) => [
      ...names
        .filter((name) => !Object.hasOwn(files, name))
        .sort((a, b) => b.length - a.length),
      ...names.filter((name) => Object.hasOwn(files, name)),
    ];

    for (const relativePath of ordered(plan.pull, remoteFiles)) {
      const file = Object.hasOwn(remoteFiles, relativePath)
        ? remoteFiles[relativePath]
        : undefined;
      await applyRemoteToLocal(localRoot, snapshot.root, relativePath, file);
      if (file) shared.set(relativePath, file);
      else shared.delete(relativePath);
    }
    for (const relativePath of ordered(plan.push, localFiles)) {
      const file = await pushLocalToRemote(
        computer,
        localRoot,
        remoteRoot,
        relativePath,
        Object.hasOwn(localFiles, relativePath)
          ? localFiles[relativePath]
          : undefined,
      );
      if (file) shared.set(relativePath, file);
      else shared.delete(relativePath);
    }
    for (const relativePath of plan.conflicts) {
      await preserveConflict(
        localRoot,
        snapshot.root,
        baseRevision.id,
        relativePath,
        remoteScan.manifest[relativePath],
      );
    }

    if (plan.conflicts.length > 0) {
      return {
        revision: baseRevision,
        conflicts: plan.conflicts,
        pulled: plan.pull.length,
        pushed: plan.push.length,
      };
    }

    // Preserve unobserved baseline entries; all other entries describe the
    // snapshots or exact bytes sent, never a later editor save.
    for (const [name, file] of Object.entries(baseRevision.files)) {
      if (excluded(name)) shared.set(name, file);
    }
    const revision = createRevision(Object.fromEntries(shared));
    await writeRemoteRevision(computer, remoteRoot, revision);
    return {
      revision,
      conflicts: [],
      pulled: plan.pull.length,
      pushed: plan.push.length,
    };
  } finally {
    await snapshot.cleanup();
  }
}

export async function createLocalBaseline(
  localRoot: string,
): Promise<WorkspaceRevision> {
  return createRevision((await scanWorkspace(localRoot)).manifest);
}
