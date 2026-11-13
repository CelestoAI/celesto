import assert from "node:assert/strict";
import { mkdir, mkdtemp, rm, symlink, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import type {
  ComputerExecResponse,
  ComputerExecStreamEvent,
  ExecParams,
} from "../src/computer.js";

import type { RemoteComputer } from "../src/operations.js";
import {
  createRevision,
  planWorkspaceSync,
  scanWorkspace,
  type WorkspaceFile,
  type WorkspaceManifest,
  uploadInitialWorkspace,
} from "../src/workspace.js";

async function temporaryDirectory(): Promise<string> {
  return mkdtemp(path.join(os.tmpdir(), "celesto-workspace-test-"));
}

const REMOTE_ROOT = "/home/celesto/workspace";

const file = (sha256: string): WorkspaceFile => ({
  sha256,
  size: 1,
  mode: 0o644,
});

class SuccessfulComputer implements RemoteComputer {
  commands: string[] = [];

  async run(command: string): Promise<ComputerExecResponse> {
    this.commands.push(command);
    return { exitCode: 0, stdout: "", stderr: "" };
  }

  async *runStream(
    _command: string,
    _params?: ExecParams,
  ): AsyncGenerator<ComputerExecStreamEvent> {
    yield { type: "exit", exitCode: 0 };
  }
}

test("scanWorkspace applies safe defaults, gitignore, celesto overrides, and file limits", async () => {
  const root = await temporaryDirectory();
  try {
    await mkdir(path.join(root, "node_modules"));
    await writeFile(
      path.join(root, "node_modules", "dependency.js"),
      "ignored",
    );
    await mkdir(path.join(root, ".pi", "agent"), { recursive: true });
    await writeFile(path.join(root, ".pi", "agent", "auth.json"), "secret");
    await writeFile(path.join(root, ".env"), "SECRET=value");
    await writeFile(path.join(root, ".env.example"), "SECRET=");
    await writeFile(
      path.join(root, ".gitignore"),
      "ignored.txt\nallowed.txt\n",
    );
    await writeFile(path.join(root, ".celestoignore"), "!allowed.txt\n");
    await writeFile(path.join(root, "ignored.txt"), "ignored");
    await writeFile(path.join(root, "allowed.txt"), "allowed");
    await writeFile(path.join(root, "large.bin"), Buffer.alloc(33));
    await writeFile(path.join(root, "target.txt"), "target");
    await symlink("target.txt", path.join(root, "link.txt"));

    const scan = await scanWorkspace(root, { maxFileBytes: 32 });
    assert(scan.files.includes(".env.example"));
    assert(scan.files.includes("allowed.txt"));
    assert(!scan.files.includes(".env"));
    assert(!scan.files.includes(".pi/agent/auth.json"));
    assert(!scan.files.includes("ignored.txt"));
    assert(!scan.files.some((entry) => entry.startsWith("node_modules/")));
    assert(!scan.files.includes("large.bin"));
    assert(!scan.files.includes("link.txt"));
    assert.equal(scan.skippedLargeFiles, 1);
    assert.equal(scan.skippedSymlinks, 1);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("uploadInitialWorkspace supports an empty project", async () => {
  const root = await temporaryDirectory();
  const computer = new SuccessfulComputer();
  try {
    const result = await uploadInitialWorkspace(computer, root, REMOTE_ROOT);
    assert.deepEqual(result.revision.files, {});
    assert(
      computer.commands.some((command) =>
        command.includes(`mv '${REMOTE_ROOT}.celesto-staging-`),
      ),
    );
    assert(!computer.commands.some((command) => command.includes("tar -xzf")));
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("createRevision is stable regardless of manifest insertion order", () => {
  const left: WorkspaceManifest = { b: file("b"), a: file("a") };
  const right: WorkspaceManifest = { a: file("a"), b: file("b") };
  assert.equal(createRevision(left).id, createRevision(right).id);
});

test("planWorkspaceSync separates pulls, pushes, equal changes, and conflicts", () => {
  const base: WorkspaceManifest = {
    "pull.txt": file("base-pull"),
    "push.txt": file("base-push"),
    "conflict.txt": file("base-conflict"),
    "remote-delete.txt": file("delete"),
    "local-delete.txt": file("delete"),
  };
  const local: WorkspaceManifest = {
    "pull.txt": file("base-pull"),
    "push.txt": file("local"),
    "conflict.txt": file("local"),
    "remote-delete.txt": file("delete"),
    "same-new.txt": file("same"),
    "local-new.txt": file("local-new"),
  };
  const remote: WorkspaceManifest = {
    "pull.txt": file("remote"),
    "push.txt": file("base-push"),
    "conflict.txt": file("remote"),
    "local-delete.txt": file("delete"),
    "same-new.txt": file("same"),
    "remote-new.txt": file("remote-new"),
  };

  assert.deepEqual(planWorkspaceSync(base, local, remote), {
    pull: ["pull.txt", "remote-delete.txt", "remote-new.txt"],
    push: ["local-delete.txt", "local-new.txt", "push.txt"],
    conflicts: ["conflict.txt"],
  });
});
