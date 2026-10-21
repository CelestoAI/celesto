"""Per-sandbox credential proxy on a real QEMU (slirp) sandbox (D-04, D-05, D-14-D-16).

Boots a disposable sandbox through the CLI, attaches a credential plan with a
sentinel value bound to ``stub.celesto.test``, and drives the guest from raw
(non-login) commands. A TLS stub on the host plays the real upstream; the
proxy reaches it only through the LaunchSpec test hook
(``test_hooks.upstream_hosts`` / ``upstream_ca_pem``).

Opt in: ``CELESTO_E2E_CREDENTIALS=1 uv run --extra dev pytest -m e2e
tests/e2e/test_credential_runtime.py``. Needs macOS or Linux with QEMU.
Writes ``artifacts/credential-runtime/e2e-summary.json``; sentinel values are
never written to it.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import ssl
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("CELESTO_E2E_CREDENTIALS") != "1",
        reason="Set CELESTO_E2E_CREDENTIALS=1 to boot a real sandbox.",
    ),
    pytest.mark.skipif(not shutil.which("openssl"), reason="Needs openssl."),
]

REAL = "sk-SENTINEL-w3runtime-" + uuid.uuid4().hex
PH = "celesto-ph-w3-" + uuid.uuid4().hex
HOST = "stub.celesto.test"
ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "artifacts" / "credential-runtime" / "e2e-summary.json"
CELESTO = str(Path(sys.executable).with_name("celesto"))
D16 = (
    "Credential protection stopped for {name}. Run 'celesto computer stop {name}' "
    "and 'celesto computer start {name}' to restore it."
)


def _openssl(*args: str, cwd: Path) -> None:
    subprocess.run(["openssl", *args], cwd=cwd, check=True, capture_output=True)


def _make_certs(directory: Path) -> tuple[Path, Path, str]:
    _openssl(
        "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "2",
        "-keyout", "ca.key", "-out", "ca.pem", "-subj", "/CN=w3 stub CA",
        "-addext", "basicConstraints=critical,CA:TRUE",
        "-addext", "keyUsage=critical,keyCertSign,cRLSign",
        cwd=directory,
    )  # fmt: skip
    _openssl(
        "req", "-newkey", "rsa:2048", "-nodes", "-keyout", "leaf.key",
        "-out", "leaf.csr", "-subj", f"/CN={HOST}", cwd=directory,
    )  # fmt: skip
    (directory / "leaf.ext").write_text(f"subjectAltName=DNS:{HOST}\nextendedKeyUsage=serverAuth\n")
    _openssl(
        "x509", "-req", "-in", "leaf.csr", "-CA", "ca.pem", "-CAkey", "ca.key",
        "-CAcreateserial", "-days", "2", "-out", "leaf.pem", "-extfile", "leaf.ext",
        cwd=directory,
    )  # fmt: skip
    return directory / "leaf.pem", directory / "leaf.key", (directory / "ca.pem").read_text()


class _Stub(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    seen: list[str] = []

    def do_GET(self) -> None:  # noqa: N802
        type(self).seen.append(self.headers.get("authorization", ""))
        body = b"stub-ok\n"
        self.send_response(200)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: Any) -> None:
        pass


@pytest.fixture
def stub(tmp_path: Path) -> Iterator[tuple[int, str]]:
    leaf, key, ca_pem = _make_certs(tmp_path)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(leaf, key)
    # 0.0.0.0 so the "ignores /etc/hosts" probe can reach it through 10.0.2.2.
    server = ThreadingHTTPServer(("0.0.0.0", 0), _Stub)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1], ca_pem
    finally:
        server.shutdown()


def _cli(env: dict[str, str], *args: str, check: bool = True) -> dict[str, Any]:
    result = subprocess.run(
        [CELESTO, *args, "--json"],
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    payload = json.loads(result.stdout) if result.stdout.strip().startswith("{") else {}
    if check and result.returncode != 0:
        raise AssertionError(f"celesto {' '.join(args)} failed: {result.stdout}{result.stderr}")
    payload["_raw"] = result.stdout + result.stderr
    return payload


def _human(env: dict[str, str], *args: str) -> str:
    result = subprocess.run(
        [CELESTO, *args],
        env={**env, "COLUMNS": "400"},
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.stdout + result.stderr


def _wait(predicate: Any, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.2)
    return predicate()


def _alive(pid: int) -> bool:
    # The launcher is this test process's child: reap it so a zombie counts as gone.
    try:
        if os.waitpid(pid, os.WNOHANG)[0] == pid:
            return False
    except ChildProcessError:
        pass
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _scan_command() -> str:
    # The value is passed hex-escaped so the scanner's own argv never holds it.
    escaped = "".join(f"\\x{byte:02x}" for byte in REAL.encode())
    # grep reads the pattern from a pipe (-f), so no argv anywhere holds it.
    pattern = f"<(printf '{escaped}')"
    script = (
        f"grep -rIlF -f {pattern} /etc /root /home /tmp /var/tmp /run 2>/dev/null; "
        "for f in /proc/[0-9]*/environ /proc/[0-9]*/cmdline; do "
        f'grep -lFa -f {pattern} "$f" 2>/dev/null; done; true'
    )
    return f"bash -c {json.dumps(script)}"


def test_credential_proxy_lifecycle_on_real_sandbox(tmp_path: Path, stub: tuple[int, str]) -> None:
    from celesto.cli.service import CLIService
    from celesto.credentials import runtime, user_secrets
    from celesto.credentials.types import Binding, CredentialPlan, GuestFile

    port, stub_ca = stub
    data_dir = tmp_path / "data"
    env = {**os.environ, "CELESTO_DATA_DIR": str(data_dir), "CELESTO_TELEMETRY": "0"}
    name = f"w3-cred-{uuid.uuid4().hex[:6]}"
    summary: dict[str, Any] = {"sandbox": name, "checks": {}}
    checks = summary["checks"]

    def raw(command: str, timeout: int = 60) -> Any:
        return vm.run(command, timeout=timeout, shell="raw")

    curl = (
        f"curl -sS -m 10 -o /dev/null -w '%{{http_code}}' "
        f"-H 'Authorization: Bearer {PH}' https://{HOST}/echo"
    )
    plan = CredentialPlan(
        bindings=[
            Binding(
                name="STUB_TOKEN",
                placeholder=PH,
                hosts=(HOST,),
                # A user secret's default rules (D-20, D-24).
                headers=user_secrets.header_rules(None),
                source="env:STUB_TOKEN",
            )
        ],
        guest_env={"STUB_TOKEN": PH},
        guest_files=[GuestFile("/root/.stub/auth.json", json.dumps({"token": PH}).encode())],
        real_values={"STUB_TOKEN": REAL},
    )
    hooks = {"upstream_hosts": {HOST: f"127.0.0.1:{port}"}, "upstream_ca_pem": stub_ca}

    vm = None
    try:
        _cli(env, "sandbox", "create", "--name", name)
        vm = CLIService(data_dir).vm_from_id(name, data_dir=data_dir)
        handle = runtime.attach(vm, plan, test_hooks=hooks)
        first_ca = raw("cat /usr/local/share/ca-certificates/celesto-sandbox.crt").stdout

        # D-04: a raw exec (no login shell) is routed by /etc/hosts and injected.
        _Stub.seen.clear()
        assert raw(curl).stdout == "200"
        assert _Stub.seen == [f"Bearer {REAL}"]
        checks["raw_exec_injected"] = True

        # D-24: gh sends `Authorization: token <t>`.
        _Stub.seen.clear()
        assert raw(curl.replace("Bearer ", "token ")).stdout == "200"
        assert _Stub.seen == [f"token {REAL}"]
        checks["token_form_injected"] = True

        hosts_file = raw("cat /etc/hosts").stdout
        assert f"10.0.2.100 {HOST}" in hosts_file
        assert f"::ffff:10.0.2.100 {HOST}" in hosts_file
        checks["hosts_block_ipv4_ipv6"] = True

        login_env = vm.run(
            "printenv STUB_TOKEN; printenv SSL_CERT_FILE; printenv NODE_EXTRA_CA_CERTS;"
            " printenv REQUESTS_CA_BUNDLE"
        )
        # D-14, D-25: every CA variable names the full system bundle.
        assert login_env.stdout.split() == [PH, *(["/etc/ssl/certs/ca-certificates.crt"] * 3)]
        assert json.loads(raw("cat /root/.stub/auth.json").stdout) == {"token": PH}
        assert raw("stat -c %a /root/.stub/auth.json").stdout.strip() == "600"
        checks["managed_env_and_guest_files"] = True

        # Bypassing /etc/hosts reaches the upstream with only the placeholder.
        _Stub.seen.clear()
        bypass = raw(
            f"curl -sk -m 10 -o /dev/null -w '%{{http_code}}' --resolve {HOST}:{port}:10.0.2.2 "
            f"-H 'Authorization: Bearer {PH}' https://{HOST}:{port}/echo"
        )
        assert bypass.stdout == "200"
        assert _Stub.seen == [f"Bearer {PH}"]
        checks["bypass_carries_placeholder_only"] = True

        # D-15: live remove is a kill switch; set restores it.
        # Proxy-only remove: the guest still routes the host to the proxy, which
        # no longer serves it, so the next request never reaches upstream.
        runtime.control(name, "remove_binding", name="STUB_TOKEN", data_dir=data_dir)
        _Stub.seen.clear()
        assert raw(curl).stdout != "200"
        assert _Stub.seen == []
        binding = {
            "name": "STUB_TOKEN",
            "placeholder": PH,
            "hosts": [HOST, f"extra.{HOST}"],
            "headers": [{"header": "authorization", "form": "bearer"}],
        }
        runtime.control(
            name, "set_binding", binding=binding, real_value=REAL, data_dir=data_dir, vm=vm
        )
        assert f"10.0.2.100 extra.{HOST}" in raw("cat /etc/hosts").stdout
        reply = runtime.control(name, "status", data_dir=data_dir)
        assert reply["bindings"] == [{"name": "STUB_TOKEN", "has_value": True}]
        assert reply["missing"] == []
        _Stub.seen.clear()
        raw(curl)
        assert _Stub.seen == [f"Bearer {REAL}"]
        # Remove with the guest: its hosts leave /etc/hosts too; set restores them.
        runtime.control(name, "remove_binding", name="STUB_TOKEN", data_dir=data_dir, vm=vm)
        assert HOST not in raw("cat /etc/hosts").stdout
        runtime.control(
            name, "set_binding", binding=binding, real_value=REAL, data_dir=data_dir, vm=vm
        )
        checks["live_remove_and_set"] = True

        status = runtime.status(name, data_dir=data_dir)
        assert status.state == "running" and status.message is None
        info = _cli(env, "sandbox", "info", name)
        assert info["data"]["credentials"]["status"] == "running"

        logs = _human(env, "sandbox", "logs", name, "--credentials")
        assert "inject" in logs and "STUB_TOKEN" in logs and REAL not in logs and PH not in logs
        checks["credential_logs"] = True

        scan = raw(_scan_command(), timeout=120).stdout.split()
        assert scan == [], scan
        checks["guest_scan_hits"] = len(scan)

        # D-14: a new attach mints a fresh CA and reinstalls it.
        handle = runtime.attach(vm, plan, test_hooks=hooks)
        second_ca = raw("cat /usr/local/share/ca-certificates/celesto-sandbox.crt").stdout
        assert second_ca.startswith("-----BEGIN CERTIFICATE-----") and second_ca != first_ca
        _Stub.seen.clear()
        assert raw(curl).stdout == "200" and _Stub.seen == [f"Bearer {REAL}"]
        checks["fresh_ca_on_reattach"] = True

        # D-16: kill the proxy; bound host fails closed, other traffic works.
        os.kill(handle.pid, signal.SIGKILL)
        assert _wait(lambda: not _alive(handle.pid))
        _Stub.seen.clear()
        assert raw(curl).stdout != "200" and _Stub.seen == []
        pypi = raw("curl -sS -m 20 -o /dev/null -w '%{http_code}' https://pypi.org/simple/")
        assert pypi.stdout == "200"
        message = D16.format(name=name)
        info = _cli(env, "sandbox", "info", name)
        assert info["data"]["credentials"]["message"] == message
        assert message in info["data"]["warnings"]
        assert message in " ".join(_human(env, "sandbox", "info", name).split())
        listed = _cli(env, "sandbox", "list")
        row = next(r for r in listed["data"]["vms"] if r["name"] == name)
        assert message in row["warnings"]
        assert message in " ".join(_human(env, "sandbox", "list").split())
        checks["proxy_killed_fails_closed"] = True
        checks["pypi_with_proxy_dead"] = pypi.stdout
        checks["d16_message_in_info_and_list"] = True

        # D-05: stopping the sandbox stops its proxy.
        handle = runtime.attach(vm, plan, test_hooks=hooks)
        _cli(env, "sandbox", "stop", name)
        assert _wait(lambda: not _alive(handle.pid), timeout=10)
        assert runtime.status(name, data_dir=data_dir).state == "not_configured"
        checks["proxy_stops_with_sandbox_stop"] = True
        _cli(env, "sandbox", "start", name)
        vm.close()
        vm = CLIService(data_dir).vm_from_id(name, data_dir=data_dir)

        # D-16: the proxy exits when the VM process exits.
        handle = runtime.attach(vm, plan, test_hooks=hooks)
        assert _alive(handle.pid)
        vm_pid = vm.info.pid
        assert vm_pid is not None
        os.kill(vm_pid, signal.SIGKILL)
        assert _wait(lambda: not _alive(handle.pid), timeout=10)
        checks["proxy_exits_with_vm"] = True
        assert not handle.control_socket.exists()
    finally:
        if vm is not None:
            vm.close()
        _cli(env, "sandbox", "delete", name, "--force", check=False)
        summary["host_artifacts_contain_real_value"] = any(
            REAL in path.read_text(errors="ignore")
            for path in data_dir.rglob("*")
            if path.is_file() and path.suffix in {".log", ".json"}
        )
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    assert summary["host_artifacts_contain_real_value"] is False
