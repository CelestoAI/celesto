"""Join an already prepared cgroup and exec QEMU without changing its PID.

This file runs with Python isolated mode and imports only the standard library.
It creates neither policies nor cgroups. The narrow, root-owned pool helper
validates the launch identity and joins this process; no cgroup is delegated.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import time
from pathlib import PurePosixPath


def main() -> None:
    try:
        group, deadline_text, separator, *command = sys.argv[1:]
        if separator != "--" or not command or not os.path.isabs(command[0]):
            raise ValueError("invalid launch command")
        deadline = None if deadline_text == "none" else float(deadline_text)
        if deadline is not None and (not math.isfinite(deadline) or deadline <= time.time()):
            raise ValueError("maximum runner lifetime expired")
        path = PurePosixPath(group)
        if not path.is_absolute() or ".." in path.parts or str(path) != group:
            raise ValueError("invalid cgroup path")
        directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            # openat + O_NOFOLLOW on every component rejects substitution by a
            # symlink, including ancestors, rather than checking then reopening.
            for part in path.parts[1:]:
                child = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                    dir_fd=directory,
                )
                os.close(directory)
                directory = child
            if deadline is not None and deadline <= time.time():
                raise ValueError("maximum runner lifetime expired")
            # Do not grant the agent write access to a shared cgroup ancestor.
            # The helper accepts identities only, checks this exact process and
            # its agent parent, and performs the privileged migration itself.
            with open("/proc/self/stat", encoding="ascii") as stat_file:
                process_stat = stat_file.read()
            starttime = process_stat[process_stat.rfind(")") + 2 :].split()[19]
            timeout = (
                min(10.0, max(0.001, deadline - time.time())) if deadline is not None else 10.0
            )
            control = os.open(
                "cgroup.procs", os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=directory
            )
            try:
                subprocess.run(
                    [
                        "/usr/bin/sudo",
                        "-n",
                        "/usr/local/sbin/celesto-pool-vm-helper",
                        "join",
                        path.name,
                        str(os.getpid()),
                        starttime,
                    ],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    check=True,
                    close_fds=True,
                    env={"PATH": os.defpath, "LANG": "C.UTF-8"},
                    timeout=timeout,
                )
                with os.fdopen(control, "r", encoding="ascii", closefd=False) as members:
                    if str(os.getpid()) not in {line.strip() for line in members}:
                        raise ValueError("resource group membership was not established")
            finally:
                os.close(control)
        finally:
            os.close(directory)
        if deadline is not None and deadline <= time.time():
            raise ValueError("maximum runner lifetime expired")
        os.execv(command[0], command)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        detail = str(exc)
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            # The helper's fixed command can refuse with an actionable reason;
            # preserve only its bounded diagnostic tail across the exec shim.
            reason = exc.stderr[-4096:].decode("utf-8", errors="replace")
            detail += ": " + " ".join(reason.split())
        print(f"QEMU launch refused: {detail}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
