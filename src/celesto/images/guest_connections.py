"""Guest-side connection setup, also executable on existing desktop images.

Only Python's standard library is used: this file runs inside the guest, not
the user's computer. The SDK sends this same source through its command channel.
"""

import fcntl
import json
import os
import pwd
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

RUNTIME = Path("/run/celesto-browser")
LOGS = Path("/var/log/celesto-browser")


def capabilities():
    common = all(shutil.which(tool) for tool in ("Xvfb", "openbox", "runuser"))
    try:
        pwd.getpwnam("agent")
    except KeyError:
        common = False
    browser = common and any(shutil.which(tool) for tool in ("chromium", "chromium-browser"))
    browser = browser and Path("/usr/local/bin/celesto-browser-session").is_file()
    display = common and all(shutil.which(tool) for tool in ("x11vnc", "websockify"))
    return {
        "version": 1,
        "browser": bool(browser),
        "read_only": bool(display),
        "read_write": bool(display),
    }


def alive(name, executable):
    try:
        pid = int((RUNTIME / (name + ".pid")).read_text().strip())
        if pid <= 1:
            return False
        os.kill(pid, 0)
        # Do not trust a stale PID file whose PID has been reused.
        args = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        return any(Path(arg.decode()).name == executable for arg in args if arg)
    except (OSError, ValueError, UnicodeError):
        return False


def listening(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def wait_for(check, deadline):
    while not check():
        if time.monotonic() >= deadline:
            raise RuntimeError("service did not become ready")
        time.sleep(0.1)


def spawn(name, executable, args, *, env=None):
    if alive(name, executable):
        return
    with (LOGS / (name + ".log")).open("ab") as log:
        proc = subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            env=env,
            start_new_session=True,
            close_fds=True,
        )
    (RUNTIME / (name + ".pid")).write_text(str(proc.pid))


def ensure(kind, timeout, proxy=None):
    if kind not in ("browser", "read_only", "read_write") or not capabilities()[kind]:
        raise RuntimeError("unsupported capability")
    deadline = time.monotonic() + timeout
    RUNTIME.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    with (RUNTIME / "connections.lock").open("a") as lock:
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RuntimeError("connection setup is busy") from None
                time.sleep(0.1)
        # Reuse an existing desktop, including one started by the legacy API.
        if not Path("/tmp/.X11-unix/X99").exists():
            spawn("xvfb", "Xvfb", ["Xvfb", ":99", "-screen", "0", "1280x720x24", "-ac"])
        wait_for(lambda: Path("/tmp/.X11-unix/X99").exists(), deadline)
        spawn(
            "openbox",
            "openbox",
            [
                "runuser",
                "-u",
                "agent",
                "--",
                "env",
                "DISPLAY=:99",
                "HOME=/home/agent",
                "openbox",
            ],
        )
        if shutil.which("tint2"):
            spawn(
                "tint2",
                "tint2",
                [
                    "runuser",
                    "-u",
                    "agent",
                    "--",
                    "env",
                    "DISPLAY=:99",
                    "HOME=/home/agent",
                    "tint2",
                ],
            )
        if kind == "browser":
            # Chromium itself listens on 9223; the legacy proxy uses 9222.
            # Reuse the browser without restarting it or changing its profile.
            if not listening(9223):
                args = [
                    "/usr/local/bin/celesto-browser-session",
                    "launch-browser",
                    "computer",
                    "1280",
                    "720",
                    "9222",
                    "/opt/celesto-browser/profiles/computer",
                    "/opt/celesto-browser/downloads/computer",
                    "1",
                ]
                if proxy:
                    args.append(proxy)
                subprocess.run(
                    args,
                    check=True,
                    capture_output=True,
                    timeout=max(0.1, deadline - time.monotonic()),
                )
            wait_for(lambda: listening(9223), deadline)
            return {"port": 9223}
        readonly = kind == "read_only"
        # Separate processes prevent a writer from changing a watcher's mode.
        # Use SDK-owned ports for both modes so legacy listeners remain intact.
        vnc_port, ws_port = (5901, 6081) if readonly else (5902, 6082)
        name = "connection-" + kind
        if listening(vnc_port) and not alive(name, "x11vnc"):
            raise RuntimeError("display port is occupied")
        spawn(
            name,
            "x11vnc",
            [
                "x11vnc",
                "-display",
                ":99",
                "-localhost",
                "-nopw",
                "-forever",
                "-shared",
                "-rfbport",
                str(vnc_port),
                *(["-viewonly"] if readonly else []),
            ],
        )
        wait_for(lambda: listening(vnc_port) and alive(name, "x11vnc"), deadline)
        if listening(ws_port) and not alive(name + "-ws", "websockify"):
            raise RuntimeError("display port is occupied")
        spawn(
            name + "-ws",
            "websockify",
            [
                "websockify",
                f"127.0.0.1:{ws_port}",
                f"127.0.0.1:{vnc_port}",
            ],
        )
        wait_for(lambda: listening(ws_port) and alive(name + "-ws", "websockify"), deadline)
        return {"port": ws_port}


def main():
    # Raw guest-agent commands inherit PID 1's minimal PATH, unlike SSH logins.
    # Both capability discovery and child processes need system administration tools.
    os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    try:
        if sys.argv[1:] == ["capabilities"]:
            result = capabilities()
        elif len(sys.argv) in (4, 5) and sys.argv[1] == "ensure":
            result = ensure(
                sys.argv[2],
                min(30.0, max(0.1, float(sys.argv[3]))),
                sys.argv[4] if len(sys.argv) == 5 else None,
            )
        else:
            raise ValueError("invalid arguments")
        print(json.dumps(result))
    except Exception:
        # Do not emit process output, browser URLs or a traceback to SDK logs.
        print(
            "Connection setup failed; inspect the computer's graphical service logs.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
