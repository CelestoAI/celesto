import assert from "node:assert/strict";
import { unlinkSync } from "node:fs";
import { execFile } from "node:child_process";
import {
  chmod,
  link,
  mkdir,
  mkdtemp,
  readFile,
  rename,
  rm,
  readdir,
  stat,
  symlink,
  writeFile,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import * as tar from "tar";
import { installLinuxCommandShims } from "./fixtures/linux-tools.js";
import {
  createCelestoBashOperations,
  readRemoteFile,
  writeRemoteFile,
  type RemoteComputer,
} from "../src/operations.js";
import type {
  ComputerExecResponse,
  ComputerExecStreamEvent,
  ExecParams,
} from "../src/computer.js";
import {
  createWorkspaceIgnore,
  downloadRemoteWorkspace,
  DEFAULT_MAX_FILE_BYTES,
  syncWorkspace,
  uploadInitialWorkspace,
} from "../src/workspace.js";

async function fixture() {
  const root = await mkdtemp(path.join(os.tmpdir(), "celesto-review-"));
  const local = path.join(root, "local");
  const remote = path.join(root, "remote");
  const bin = path.join(root, "bin");
  await Promise.all([mkdir(local), mkdir(remote), mkdir(bin)]);
  await installLinuxCommandShims(bin);
  class ShellComputer implements RemoteComputer {
    beforeRun?: (command: string) => Promise<void>;
    transfers: string[] = [];
    commands: string[] = [];
    async run(
      command: string,
      params?: ExecParams,
    ): Promise<ComputerExecResponse> {
      this.commands.push(command);
      assert(
        command.length <= 10_000,
        `Cloud command is ${command.length} characters`,
      );
      await this.beforeRun?.(command);
      return new Promise((resolve) => {
        const child = execFile(
          "/bin/sh",
          [],
          {
            encoding: "utf8",
            timeout: 10_000,
            maxBuffer: 16 * 1024 * 1024,
            signal: params?.signal,
            env: {
              ...process.env,
              COPYFILE_DISABLE: "1",
              PATH: `${bin}${path.delimiter}${process.env.PATH}`,
            },
          },
          (error, stdout, stderr) =>
            resolve({
              exitCode: error
                ? typeof error.code === "number"
                  ? error.code
                  : 1
                : 0,
              stdout,
              stderr,
            }),
        );
        child.stdin?.end(command);
      });
    }
    async *runStream(
      command: string,
      params?: ExecParams,
    ): AsyncGenerator<ComputerExecStreamEvent> {
      const result = await this.run(command, params);
      if (command.includes("base64") && result.stdout)
        this.transfers.push(result.stdout);
      if (result.stdout) yield { type: "stdout", data: result.stdout };
      if (result.stderr) yield { type: "stderr", data: result.stderr };
      yield { type: "exit", exitCode: result.exitCode };
    }
  }
  return {
    root,
    local,
    remote,
    bin,
    computer: new ShellComputer(),
    cleanup: () => rm(root, { recursive: true, force: true }),
  };
}

test("Bash tools support source, arrays and process substitution", async () => {
  const f = await fixture();
  try {
    await writeFile(path.join(f.remote, "activate"), "export ACTIVATED=yes\n");
    const output: Buffer[] = [];
    const result = await createCelestoBashOperations(
      f.computer,
      f.local,
      f.remote,
    ).exec(
      'printf "%s\\n" "$0"; source ./activate; values=(one two); printf "%s %s\\n" "$ACTIVATED" "${values[1]}"; cat <(printf substitution)',
      f.remote,
      { onData: (data) => output.push(data) },
    );
    assert.equal(result.exitCode, 0);
    assert.equal(
      Buffer.concat(output).toString(),
      "bash\nyes two\nsubstitution",
    );
  } finally {
    await f.cleanup();
  }
});

test("replacing a remote file preserves ordinary permissions", async () => {
  const f = await fixture();
  try {
    for (const mode of [0o755, 0o664, 0o444]) {
      const file = path.join(f.remote, `mode-${mode}`);
      await writeFile(file, "old");
      await chmod(file, mode);
      await writeRemoteFile(f.computer, file, "updated");
      assert.equal(await readFile(file, "utf8"), "updated");
      assert.equal((await stat(file)).mode & 0o777, mode);
    }
  } finally {
    await f.cleanup();
  }
});

test("initial transfer preserves ordinary file modes without false sync changes", async () => {
  const f = await fixture();
  try {
    await writeFile(path.join(f.local, "shared.txt"), "shared");
    await chmod(path.join(f.local, "shared.txt"), 0o664);
    await writeFile(path.join(f.local, "run.sh"), "#!/bin/sh\n");
    await chmod(path.join(f.local, "run.sh"), 0o755);
    const { revision } = await uploadInitialWorkspace(
      f.computer,
      f.local,
      f.remote,
    );
    assert.equal(
      (await stat(path.join(f.remote, "shared.txt"))).mode & 0o777,
      0o664,
    );
    assert.equal(
      (await stat(path.join(f.remote, "run.sh"))).mode & 0o777,
      0o755,
    );
    const result = await syncWorkspace(f.computer, f.local, f.remote, revision);
    assert.equal(result.pulled + result.pushed + result.conflicts.length, 0);
  } finally {
    await f.cleanup();
  }
});

test("oversized tracked files do not delete their counterpart", async (t) => {
  for (const side of ["local", "remote"] as const)
    await t.test(side, async () => {
      const f = await fixture();
      try {
        await writeFile(path.join(f.local, "tracked.bin"), "base");
        const { revision } = await uploadInitialWorkspace(
          f.computer,
          f.local,
          f.remote,
        );
        await writeFile(
          path.join(f[side], "tracked.bin"),
          Buffer.alloc(DEFAULT_MAX_FILE_BYTES + 1).fill(
            "oversized-file-fixture-0123456789",
          ),
        );
        const result = await syncWorkspace(
          f.computer,
          f.local,
          f.remote,
          revision,
        );
        const other = side === "local" ? f.remote : f.local;
        assert.equal(
          await readFile(path.join(other, "tracked.bin"), "utf8"),
          "base",
        );
        assert.deepEqual(
          result.revision.files["tracked.bin"],
          revision.files["tracked.bin"],
        );
      } finally {
        await f.cleanup();
      }
    });
});

test("failed reads and partial archives cannot become successful snapshots", async (t) => {
  await t.test("file read", async () => {
    const f = await fixture();
    try {
      await assert.rejects(
        readRemoteFile(f.computer, path.join(f.remote, "missing.txt")),
        /Read .*failed/,
      );
    } finally {
      await f.cleanup();
    }
  });
  await t.test("valid partial archive with failed tar", async () => {
    const f = await fixture();
    try {
      await writeFile(path.join(f.local, "protected.txt"), "preserve");
      await writeFile(path.join(f.local, "other.txt"), "other");
      const { revision } = await uploadInitialWorkspace(
        f.computer,
        f.local,
        f.remote,
      );
      await writeFile(
        path.join(f.bin, "tar"),
        '#!/bin/sh\n/usr/bin/tar --exclude=protected.txt "$@"\nexit 2\n',
        { mode: 0o755 },
      );
      await assert.rejects(
        syncWorkspace(f.computer, f.local, f.remote, revision),
        /Download .*failed/,
      );
      assert.equal(
        await readFile(path.join(f.local, "protected.txt"), "utf8"),
        "preserve",
      );
    } finally {
      await f.cleanup();
    }
  });
});

test("directory and file replacements converge in both directions", async (t) => {
  for (const side of ["local", "remote"] as const)
    for (const fromDirectory of [true, false]) {
      await t.test(
        `${side}: ${fromDirectory ? "directory to file" : "file to directory"}`,
        async () => {
          const f = await fixture();
          try {
            const old = fromDirectory
              ? path.join(f.local, "pkg", "sub", "old.txt")
              : path.join(f.local, "pkg");
            await mkdir(path.dirname(old), { recursive: true });
            await writeFile(old, "base");
            const { revision } = await uploadInitialWorkspace(
              f.computer,
              f.local,
              f.remote,
            );
            await rm(path.join(f[side], "pkg"), {
              recursive: true,
              force: true,
            });
            const replacement = fromDirectory ? "pkg" : "pkg/sub/new.txt";
            await mkdir(path.dirname(path.join(f[side], replacement)), {
              recursive: true,
            });
            await writeFile(path.join(f[side], replacement), "replacement");
            const result = await syncWorkspace(
              f.computer,
              f.local,
              f.remote,
              revision,
            );
            assert.deepEqual(result.conflicts, []);
            for (const tree of [f.local, f.remote])
              assert.equal(
                await readFile(path.join(tree, replacement), "utf8"),
                "replacement",
              );
            const again = await syncWorkspace(
              f.computer,
              f.local,
              f.remote,
              result.revision,
            );
            assert.equal(
              again.pulled + again.pushed + again.conflicts.length,
              0,
            );
          } finally {
            await f.cleanup();
          }
        },
      );
    }
});

test("shape replacements preserve independently added children as conflicts", async (t) => {
  for (const side of ["local", "remote"] as const)
    await t.test(side, async () => {
      const f = await fixture();
      try {
        await mkdir(path.join(f.local, "pkg"));
        await writeFile(path.join(f.local, "pkg", "tracked.txt"), "base");
        const { revision } = await uploadInitialWorkspace(
          f.computer,
          f.local,
          f.remote,
        );
        const other = side === "local" ? f.remote : f.local;
        await writeFile(
          path.join(other, "pkg", "independent.txt"),
          "independent",
        );
        await rm(path.join(f[side], "pkg"), { recursive: true });
        await writeFile(path.join(f[side], "pkg"), "replacement");
        const result = await syncWorkspace(
          f.computer,
          f.local,
          f.remote,
          revision,
        );
        assert(result.conflicts.includes("pkg"));
        assert.equal(
          await readFile(path.join(other, "pkg", "independent.txt"), "utf8"),
          "independent",
        );
        assert.equal(
          await readFile(path.join(other, "pkg", "tracked.txt"), "utf8"),
          "base",
        );
        assert.equal(
          await readFile(path.join(f[side], "pkg"), "utf8"),
          "replacement",
        );
      } finally {
        await f.cleanup();
      }
    });
});

test("edits during upload remain pending instead of becoming shared state", async () => {
  const f = await fixture();
  try {
    await writeFile(path.join(f.local, "later.txt"), "base");
    await writeFile(path.join(f.local, "upload.txt"), "base");
    const { revision } = await uploadInitialWorkspace(
      f.computer,
      f.local,
      f.remote,
    );
    await writeFile(path.join(f.local, "upload.txt"), "upload-version");
    let changed = false;
    f.computer.beforeRun = async (command) => {
      if (!changed && command.includes(path.join(f.remote, "upload.txt"))) {
        changed = true;
        await writeFile(path.join(f.local, "later.txt"), "late-edit");
        await writeFile(path.join(f.local, "upload.txt"), "late-upload-edit");
      }
    };
    const first = await syncWorkspace(f.computer, f.local, f.remote, revision);
    assert(changed);
    assert.equal(
      await readFile(path.join(f.remote, "later.txt"), "utf8"),
      "base",
    );
    assert.equal(
      await readFile(path.join(f.remote, "upload.txt"), "utf8"),
      "upload-version",
    );
    const second = await syncWorkspace(
      f.computer,
      f.local,
      f.remote,
      first.revision,
    );
    assert.deepEqual(second.conflicts, []);
    for (const tree of [f.local, f.remote]) {
      assert.equal(
        await readFile(path.join(tree, "later.txt"), "utf8"),
        "late-edit",
      );
      assert.equal(
        await readFile(path.join(tree, "upload.txt"), "utf8"),
        "late-upload-edit",
      );
    }
  } finally {
    await f.cleanup();
  }
});

test("writing a directory fails without depositing a temporary file inside it", async () => {
  const f = await fixture();
  try {
    const directory = path.join(f.remote, "directory");
    await mkdir(directory);
    await writeFile(path.join(directory, "keep.txt"), "keep");
    await assert.rejects(writeRemoteFile(f.computer, directory, "new"));
    assert.deepEqual(
      await (await import("node:fs/promises")).readdir(directory),
      ["keep.txt"],
    );
  } finally {
    await f.cleanup();
  }
});

test("failed archive creation cleans up its owned temporary directory", async () => {
  const f = await fixture();
  const originalTmpdir = os.tmpdir;
  try {
    const temp = path.join(f.root, "archive-temp");
    await mkdir(temp);
    const file = path.join(f.local, "vanishing.txt");
    await writeFile(file, "scan then disappear");
    let removed = false;
    os.tmpdir = () => {
      if (!removed) {
        removed = true;
        unlinkSync(file);
      }
      return temp;
    };
    await assert.rejects(uploadInitialWorkspace(f.computer, f.local, f.remote));
    os.tmpdir = originalTmpdir;
    assert.deepEqual(
      await (await import("node:fs/promises")).readdir(temp),
      [],
    );
  } finally {
    os.tmpdir = originalTmpdir;
    await f.cleanup();
  }
});

// This guards the transfer boundary: scanning only after extraction leaks
// ignored bytes and lets excluded compressible files reject the whole sync.
test("remote exclusions stay out of the transferred archive", async () => {
  const f = await fixture();
  try {
    await mkdir(path.join(f.remote, "node_modules"));
    await writeFile(path.join(f.remote, ".env"), "SECRET=must-not-transfer");
    await writeFile(
      path.join(f.remote, "node_modules", "ignored.bin"),
      Buffer.alloc(DEFAULT_MAX_FILE_BYTES + 1),
    );
    await writeFile(
      path.join(f.remote, "oversized.bin"),
      Buffer.alloc(DEFAULT_MAX_FILE_BYTES + 1),
    );
    await writeFile(
      path.join(f.remote, "selected.bin"),
      Buffer.alloc(1024 * 1024),
    );
    await writeFile(path.join(f.remote, "-file\nwith newline.txt"), "allowed");
    const snapshot = await downloadRemoteWorkspace(
      f.computer,
      f.remote,
      await createWorkspaceIgnore(f.local),
    );
    try {
      assert.equal(
        (await readFile(path.join(snapshot.root, "selected.bin"))).length,
        1024 * 1024,
      );
      assert.equal(
        await readFile(
          path.join(snapshot.root, "-file\nwith newline.txt"),
          "utf8",
        ),
        "allowed",
      );
      assert(snapshot.excludedPaths.includes(".env"));
      assert(snapshot.excludedPaths.includes("oversized.bin"));
      assert(snapshot.excludedPaths.includes("node_modules"));
      assert.deepEqual(snapshot.excludedPaths.sort(), [
        ".env",
        "node_modules",
        "oversized.bin",
      ]);
      assert.equal(f.computer.transfers.length, 1);
      const wire = path.join(f.root, "wire.tgz");
      await writeFile(wire, Buffer.from(f.computer.transfers[0]!, "base64"));
      const entries: string[] = [];
      await tar.t({
        file: wire,
        onReadEntry: (entry) => entries.push(entry.path.replace(/^\.\//, "")),
      });
      assert.deepEqual(entries.sort(), [
        "-file\nwith newline.txt",
        "selected.bin",
      ]);
    } finally {
      await snapshot.cleanup();
    }
  } finally {
    await f.cleanup();
  }
});

test("changed remote symlink ancestors cannot transfer outside file contents", async () => {
  const f = await fixture();
  try {
    const folder = "dir\n";
    await mkdir(path.join(f.local, folder));
    await writeFile(path.join(f.local, folder, "file.txt"), "tracked");
    const { revision } = await uploadInitialWorkspace(
      f.computer,
      f.local,
      f.remote,
    );
    const baseline = JSON.parse(JSON.stringify(revision));
    const outside = path.join(f.root, "outside");
    await mkdir(outside);
    await writeFile(path.join(outside, "file.txt"), "private");
    let changed = false;
    f.computer.beforeRun = async (command) => {
      if (!changed && command.includes("tar --null")) {
        changed = true;
        await rename(
          path.join(f.remote, folder),
          path.join(f.remote, "original-dir"),
        );
        await symlink(outside, path.join(f.remote, folder));
      }
    };

    await assert.rejects(
      syncWorkspace(f.computer, f.local, f.remote, revision),
      /Download .*failed/,
    );
    assert(changed);
    assert.equal(
      await readFile(path.join(f.local, folder, "file.txt"), "utf8"),
      "tracked",
    );
    assert.deepEqual(revision, baseline);
    assert.deepEqual(f.computer.transfers, []);
  } finally {
    await f.cleanup();
  }
});

// Value: protects=excluded hardlink contents stay off the download wire;
// fails_when=a selected file becomes a hardlink after metadata inspection;
// why_new=the static hardlink test only covers links present during inspection; seam=none
test("a selected remote file becoming a hardlink aborts before download", async () => {
  const f = await fixture();
  let snapshot: Awaited<ReturnType<typeof downloadRemoteWorkspace>> | undefined;
  try {
    const selected = path.join(f.remote, "selected.txt");
    const outside = path.join(f.root, "outside.txt");
    await writeFile(selected, "visible");
    await writeFile(outside, "private");
    let changed = false;
    f.computer.beforeRun = async (command) => {
      if (!changed && command.includes("tar --null")) {
        changed = true;
        await rm(selected);
        await link(outside, selected);
      }
    };
    await assert.rejects(async () => {
      snapshot = await downloadRemoteWorkspace(
        f.computer,
        f.remote,
        await createWorkspaceIgnore(f.local),
      );
    }, /Download .*failed/);
    assert(changed);
    assert.deepEqual(f.computer.transfers, []);
    assert.equal(await readFile(outside, "utf8"), "private");
  } finally {
    await snapshot?.cleanup();
    await f.cleanup();
  }
});

test("remote hardlinks stay excluded without deleting tracked counterparts", async () => {
  const f = await fixture();
  try {
    await writeFile(path.join(f.local, "tracked-a.txt"), "tracked-a");
    await writeFile(path.join(f.local, "tracked-b.txt"), "tracked-b");
    await writeFile(path.join(f.local, "selected.txt"), "selected");
    const { revision } = await uploadInitialWorkspace(
      f.computer,
      f.local,
      f.remote,
    );
    await rm(path.join(f.remote, "tracked-b.txt"));
    await link(
      path.join(f.remote, "tracked-a.txt"),
      path.join(f.remote, "tracked-b.txt"),
    );
    assert.equal((await stat(path.join(f.remote, "tracked-a.txt"))).nlink, 2);
    const snapshot = await downloadRemoteWorkspace(
      f.computer,
      f.remote,
      await createWorkspaceIgnore(f.local),
    );
    try {
      for (const name of ["tracked-a.txt", "tracked-b.txt"])
        assert(snapshot.excludedPaths.includes(name));
      assert.equal(
        await readFile(path.join(snapshot.root, "selected.txt"), "utf8"),
        "selected",
      );
      assert.equal(f.computer.transfers.length, 1);
      const wire = path.join(f.root, "wire.tgz");
      await writeFile(wire, Buffer.from(f.computer.transfers[0]!, "base64"));
      const entries: string[] = [];
      await tar.t({
        file: wire,
        onReadEntry: (entry) => entries.push(entry.path.replace(/^\.\//, "")),
      });
      assert.deepEqual(entries, ["selected.txt"]);
    } finally {
      await snapshot.cleanup();
    }
    const result = await syncWorkspace(f.computer, f.local, f.remote, revision);
    assert.equal(result.pulled + result.pushed + result.conflicts.length, 0);
    for (const name of ["tracked-a.txt", "tracked-b.txt"]) {
      assert.equal(
        await readFile(path.join(f.local, name), "utf8"),
        path.parse(name).name,
      );
      assert.deepEqual(result.revision.files[name], revision.files[name]);
    }
  } finally {
    await f.cleanup();
  }
});

// An obsolete baseline file must not hide live eligible children merely because
// an ignored descendant exists beside them. The public sync must merge the tree.
test("ignored children do not stall a tracked file replaced by directories on both sides", async (t) => {
  for (const ignoredSide of ["local", "remote"] as const) {
    await t.test(ignoredSide, async () => {
      const f = await fixture();
      try {
        await writeFile(path.join(f.local, "pkg"), "baseline file");
        const { revision } = await uploadInitialWorkspace(
          f.computer,
          f.local,
          f.remote,
        );
        for (const side of ["local", "remote"] as const) {
          await rm(path.join(f[side], "pkg"));
          await mkdir(path.join(f[side], "pkg"));
          await writeFile(
            path.join(f[side], "pkg", `${side}.txt`),
            `${side} edit`,
          );
        }
        const secret = path.join(f[ignoredSide], "pkg", ".env");
        await writeFile(secret, "PRIVATE=preserve");
        const result = await syncWorkspace(
          f.computer,
          f.local,
          f.remote,
          revision,
        );
        assert.deepEqual(result.conflicts, []);
        for (const side of ["local", "remote"] as const) {
          assert.equal(
            await readFile(path.join(f[side], "pkg", "local.txt"), "utf8"),
            "local edit",
          );
          assert.equal(
            await readFile(path.join(f[side], "pkg", "remote.txt"), "utf8"),
            "remote edit",
          );
        }
        assert.equal(await readFile(secret, "utf8"), "PRIVATE=preserve");
        assert(!Object.hasOwn(result.revision.files, "pkg"));
        const retry = await syncWorkspace(
          f.computer,
          f.local,
          f.remote,
          result.revision,
        );
        assert.equal(retry.pulled + retry.pushed + retry.conflicts.length, 0);
      } finally {
        await f.cleanup();
      }
    });
  }
});

test("a changed remote ancestor is rejected before upload staging", async () => {
  const f = await fixture();
  try {
    await mkdir(path.join(f.local, "dir"));
    await writeFile(path.join(f.local, "dir", "kept.txt"), "baseline");
    const { revision } = await uploadInitialWorkspace(
      f.computer,
      f.local,
      f.remote,
    );
    await mkdir(path.join(f.local, "dir", "new"));
    await writeFile(
      path.join(f.local, "dir", "new", "file.txt"),
      "private upload",
    );
    const outside = path.join(f.root, "outside");
    await mkdir(outside);
    await writeFile(path.join(outside, "keep.txt"), "outside");
    let changed = false;
    f.computer.beforeRun = async (command) => {
      if (
        !changed &&
        command.includes("mkdir -p") &&
        command.includes(path.join(f.remote, "dir", "new"))
      ) {
        changed = true;
        await rename(
          path.join(f.remote, "dir"),
          path.join(f.remote, "original-dir"),
        );
        await symlink(outside, path.join(f.remote, "dir"));
      }
    };
    await assert.rejects(
      syncWorkspace(f.computer, f.local, f.remote, revision),
      /changed during sync/i,
    );
    assert(changed);
    assert.deepEqual(await readdir(outside), ["keep.txt"]);
    assert.equal(
      await readFile(path.join(outside, "keep.txt"), "utf8"),
      "outside",
    );
  } finally {
    await f.cleanup();
  }
});

test("failed remote preparation cleans files created before the failure", async () => {
  const f = await fixture();
  try {
    const interrupted: RemoteComputer = {
      run: (command, params) =>
        f.computer.run(
          command.includes("umask 077") ? `${command}; false` : command,
          params,
        ),
      runStream: (command, params) => f.computer.runStream(command, params),
    };
    await assert.rejects(
      writeRemoteFile(interrupted, path.join(f.remote, "file.txt"), "content", {
        root: f.remote,
      }),
      /Prepare .*failed/,
    );
    assert.deepEqual(await readdir(f.remote), []);
  } finally {
    await f.cleanup();
  }
});

test("deep quoted paths sync large files within the Cloud command limit", async () => {
  const f = await fixture();
  try {
    await writeFile(path.join(f.local, "seed.txt"), "baseline");
    let { revision } = await uploadInitialWorkspace(
      f.computer,
      f.local,
      f.remote,
    );
    const relative = [
      ...Array.from(
        { length: process.platform === "linux" ? 30 : 9 },
        (_, index) => `part-${index}-${"x".repeat(72)}'`,
      ),
      "payload.bin",
    ].join("/");
    const local = path.join(f.local, relative);
    const remote = path.join(f.remote, relative);
    assert(remote.length >= 780);
    await mkdir(path.dirname(local), { recursive: true });
    for (const [size, byte] of [
      [20000, 0xab],
      [18000, 0xcd],
    ] as const) {
      const content = Buffer.alloc(size, byte);
      await writeFile(local, content);
      await chmod(local, 0o664);
      const result = await syncWorkspace(
        f.computer,
        f.local,
        f.remote,
        revision,
      );
      assert.deepEqual(result.conflicts, []);
      assert.deepEqual(await readFile(remote), content);
      assert.equal((await stat(remote)).mode & 0o777, 0o664);
      revision = result.revision;
    }
    if (process.env.PI_TEST_ARTIFACT_DIR) {
      const directory = process.env.PI_TEST_ARTIFACT_DIR;
      await mkdir(directory, { recursive: true });
      const transferred = await readFile(remote);
      await writeFile(
        path.join(directory, "deep-path-result.bin"),
        transferred,
      );
      await writeFile(
        path.join(directory, "deep-path-sync.json"),
        JSON.stringify(
          {
            platform: process.platform,
            pathCharacters: remote.length,
            maxCommandCharacters: Math.max(
              ...f.computer.commands.map((command) => command.length),
            ),
            commandCount: f.computer.commands.length,
            finalBytes: transferred.length,
          },
          null,
          2,
        ),
      );
    }
  } finally {
    await f.cleanup();
  }
});
