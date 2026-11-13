import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import {
  chmod,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  stat,
  writeFile,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
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
    async run(
      command: string,
      params?: ExecParams,
    ): Promise<ComputerExecResponse> {
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
    const { revision } = await uploadInitialWorkspace(
      f.computer,
      f.local,
      f.remote,
    );
    assert.equal(
      (await stat(path.join(f.remote, "shared.txt"))).mode & 0o777,
      0o664,
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
