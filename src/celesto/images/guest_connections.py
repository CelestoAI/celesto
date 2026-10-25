"""Guest-side connection setup, also executable on existing desktop images.

Only Python's standard library is used: this file runs inside the guest, not
the user's computer. The SDK sends this same source through its command channel.
"""

import fcntl
import json
import os
import pwd
import secrets
import shutil
import socket
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TypedDict


class ConnectionAccess(TypedDict):
    port: int
    capability: str


ACCESS_SOURCE = globals().get("ACCESS_SOURCE", "")  # Injected by the SDK.

RUNTIME = Path("/run/celesto-browser")
LOGS = Path("/var/log/celesto-browser")

# Published desktop images are released independently from the SDK. Keep this
# helper able to start a browser on images built before the Celesto rename;
# the host sends this script to the guest at connection time.
_BROWSER_SESSION = next(
    (
        path
        for path in (
            Path("/usr/local/bin/celesto-browser-session"),
            Path("/usr/local/bin/smolvm-browser-session"),
        )
        if path.is_file()
    ),
    Path("/usr/local/bin/celesto-browser-session"),
)
_BROWSER_ROOT = next(
    (path for path in (Path("/opt/celesto-browser"), Path("/opt/smolvm-browser")) if path.is_dir()),
    Path("/opt/celesto-browser"),
)


def private_runtime() -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    info = RUNTIME.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
        raise RuntimeError("unsafe connection folder")
    RUNTIME.chmod(0o700)
    LOGS.mkdir(parents=True, exist_ok=True)


def stop(name: str, executable: str, deadline: float) -> None:
    for directory in (RUNTIME, Path("/run/smolvm-browser")):
        if not directory.exists():
            continue
        info = directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise RuntimeError("unsafe legacy connection folder")
        if alive(name, executable, directory):
            pid = int((directory / (name + ".pid")).read_text())
            os.kill(pid, 15)

            def stopped(directory: Path = directory) -> bool:
                return not alive(name, executable, directory)

            wait_for(stopped, deadline)
        (directory / (name + ".pid")).unlink(missing_ok=True)


def protect(kind: str, port: int, target_port: int, deadline: float) -> ConnectionAccess:
    """Expose only a capability gateway; the actual service stays on loopback."""
    private_runtime()
    token_path = RUNTIME / ("access-" + kind + ".token")
    try:
        fd = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        info = token_path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o077:
            raise RuntimeError("unsafe connection credential") from None
    else:
        with os.fdopen(fd, "w") as file:
            file.write(secrets.token_hex(32))
    name = "access-" + kind
    if listening(port) and not alive(name, "python3"):
        raise RuntimeError("connection port is occupied")
    # ACCESS_SOURCE is supplied by the SDK with this file, so existing images
    # receive the same gateway implementation without downloading code.
    spawn(
        name,
        "python3",
        ["python3", "-c", ACCESS_SOURCE, str(port), str(target_port), str(token_path)],
    )
    wait_for(lambda: listening(port) and alive(name, "python3"), deadline)
    return {"port": port, "capability": token_path.read_text().strip()}


def secure_launcher(arguments: Sequence[str]) -> None:
    """Run old or new packaged launchers with every backing service on loopback.

    Refuse unfamiliar launcher layouts. Binding changes happen before launch,
    so a QEMU host forward or guest IP never exposes a passwordless service.
    """
    private_runtime()
    source = (
        _BROWSER_SESSION.read_text()
        .replace("/run/smolvm-browser", str(RUNTIME))
        .replace("/var/log/smolvm-browser", str(LOGS))
    )
    substitutions = (
        ('ThreadingServer(("0.0.0.0", listen_port)', 'ThreadingServer(("127.0.0.1", listen_port)'),
        ("x11vnc -display :99 -nopw", "x11vnc -display :99 -localhost -nopw"),
        (
            'websockify --web="${NOVNC_WEB_ROOT}" "${live_port}"',
            'websockify --web="${NOVNC_WEB_ROOT}" "127.0.0.1:${live_port}"',
        ),
    )
    for old, new in substitutions:
        if old in source:
            source = source.replace(old, new)
        elif new not in source:
            raise RuntimeError("unsupported browser launcher; rebuild the image")
    # The image's in-guest automation runner uses Chromium directly. It is not
    # a host-facing endpoint and does not need access to the gateway token.
    for root in ("celesto", "smolvm"):
        runner = Path("/usr/local/bin") / (root + "-browser-runner")
        if runner.is_file():
            text = runner.read_text().replace("http://127.0.0.1:9222", "http://127.0.0.1:9223")
            runner.write_text(text)
    launcher = RUNTIME / "secure-session.sh"
    launcher.write_text(source)
    subprocess.run(["sh", str(launcher), *arguments], check=True, capture_output=True, timeout=60)


def start_legacy(arguments: list[str]) -> dict[str, ConnectionAccess]:
    if len(arguments) not in (10, 11):
        raise ValueError("invalid session options")
    mode = arguments[0]
    if mode not in ("headless", "live", "desktop", "computer"):
        raise ValueError("invalid mode")
    if arguments[3:5] != ["9222", "6080"]:
        raise ValueError("unsupported session ports")
    # noVNC's unauthenticated backing listener is never the published 6080.
    arguments[4] = "6180"
    secure_launcher(["start", *arguments])
    return session_access(mode)


def session_access(mode: str) -> dict[str, ConnectionAccess]:
    """Secure a running legacy session without restarting its Chromium profile."""
    if mode not in ("headless", "live", "desktop", "computer"):
        raise ValueError("invalid mode")
    private_runtime()
    deadline = time.monotonic() + 30
    result = {}
    if mode != "desktop":
        stop("cdp-proxy", "python3", deadline)
        wait_for(lambda: not listening(9222) or alive("access-browser", "python3"), deadline)
        result["browser"] = protect("browser", 9222, 9223, deadline)
    if mode in ("live", "desktop", "computer"):
        # Existing images may still have public, passwordless display services.
        # Retire those processes before exposing the authenticated viewer.
        if not alive("access-viewer", "python3"):
            stop("websockify", "websockify", deadline)
            stop("x11vnc", "x11vnc", deadline)
            wait_for(lambda: not listening(5900) and not listening(6080), deadline)
            spawn(
                "x11vnc",
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
                    "5900",
                ],
            )
            wait_for(lambda: listening(5900), deadline)
            spawn(
                "websockify",
                "websockify",
                ["websockify", "--web=/usr/share/novnc", "127.0.0.1:6180", "127.0.0.1:5900"],
            )
            wait_for(lambda: listening(6180), deadline)
        result["viewer"] = protect("viewer", 6080, 6180, deadline)
    return result


def capabilities() -> dict[str, int | bool]:
    common = all(shutil.which(tool) for tool in ("Xvfb", "openbox", "runuser"))
    try:
        pwd.getpwnam("agent")
    except KeyError:
        common = False
    browser = common and any(shutil.which(tool) for tool in ("chromium", "chromium-browser"))
    browser = browser and _BROWSER_SESSION.is_file()
    display = common and all(shutil.which(tool) for tool in ("x11vnc", "websockify"))
    return {
        "version": 1,
        "browser": bool(browser),
        "read_only": bool(display),
        "read_write": bool(display),
    }


def alive(name: str, executable: str, directory: Path | None = None) -> bool:
    directory = directory or RUNTIME
    try:
        pid = int((directory / (name + ".pid")).read_text().strip())
        if pid <= 1:
            return False
        os.kill(pid, 0)
        # Do not trust a stale PID file whose PID has been reused.
        args = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        return any(Path(arg.decode()).name == executable for arg in args if arg)
    except (OSError, ValueError, UnicodeError):
        return False


def listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def wait_for(check: Callable[[], bool], deadline: float) -> None:
    while not check():
        if time.monotonic() >= deadline:
            raise RuntimeError("service did not become ready")
        time.sleep(0.1)


def spawn(
    name: str, executable: str, args: Sequence[str], *, env: Mapping[str, str] | None = None
) -> None:
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


def ensure(kind: str, timeout: float, proxy: str | None = None) -> ConnectionAccess:
    if kind not in ("browser", "read_only", "read_write") or not capabilities()[kind]:
        raise RuntimeError("unsupported capability")
    deadline = time.monotonic() + timeout
    private_runtime()
    with (RUNTIME / "connections.lock").open("a") as lock:
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RuntimeError("connection setup is busy") from None
                time.sleep(0.1)
        stop("cdp-proxy", "python3", deadline)
        if not alive("access-viewer", "python3"):
            stop("websockify", "websockify", deadline)
            stop("x11vnc", "x11vnc", deadline)
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
                    str(_BROWSER_SESSION),
                    "launch-browser",
                    "computer",
                    "1280",
                    "720",
                    "9222",
                    str(_BROWSER_ROOT / "profiles/computer"),
                    str(_BROWSER_ROOT / "downloads/computer"),
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
            # Close a legacy public proxy before binding the capability gate.
            stop("cdp-proxy", "python3", deadline)
            wait_for(lambda: not listening(9222) or alive("access-browser", "python3"), deadline)
            return protect("browser", 9222, 9223, deadline)
        readonly = kind == "read_only"
        # Separate processes prevent a writer from changing a watcher's mode.
        # Use SDK-owned ports for both modes so legacy listeners remain intact.
        vnc_port, ws_port = (5901, 6181) if readonly else (5902, 6182)
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
        return protect(kind, 6081 if readonly else 6082, ws_port, deadline)


def main() -> int:
    # Raw guest-agent commands inherit PID 1's minimal PATH, unlike SSH logins.
    # Both capability discovery and child processes need system administration tools.
    os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    result: dict[str, int | bool] | dict[str, ConnectionAccess] | ConnectionAccess
    try:
        if sys.argv[1:] == ["capabilities"]:
            result = capabilities()
        elif len(sys.argv) == 3 and sys.argv[1] == "session-access":
            result = session_access(sys.argv[2])
        elif len(sys.argv) == 3 and sys.argv[1] == "start-session":
            result = start_legacy(json.loads(sys.argv[2]))
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
