"""Opt-in smoke test that creates one billable Celesto Cloud computer."""

import os
import time
from pathlib import Path

import httpx
import pytest

from celesto import CommandExitEvent, CommandOutputEvent, Computer, PublishedPort, VMNotFoundError


def assert_public_application(url: str) -> None:
    """Allow bounded route/application readiness without retrying publication."""
    deadline = time.monotonic() + 30
    with httpx.Client(timeout=5) as client:
        while time.monotonic() < deadline:
            try:
                response = client.get(url + "/probe.txt")
            except httpx.TransportError:
                pass
            else:
                if response.status_code == 200 and response.text == "celesto-port-smoke":
                    return
            time.sleep(0.5)
    pytest.fail("Published test application did not become reachable within 30 seconds.")


@pytest.mark.skipif(
    os.getenv("CELESTO_LIVE_TEST") != "1",
    reason="Set CELESTO_LIVE_TEST=1 to create a billable cloud computer.",
)
def test_cloud_live_lifecycle():
    if not os.getenv("CELESTO_API_KEY"):
        pytest.fail("Set CELESTO_API_KEY before running the live cloud test.")

    comp = Computer()
    attached = None
    computer_id_file_value = os.getenv("CELESTO_LIVE_COMPUTER_ID_FILE")
    computer_id_file = Path(computer_id_file_value) if computer_id_file_value else None
    try:
        assert comp.id is None
        with comp:
            assert comp.id is not None
            if computer_id_file is not None:
                computer_id_file.parent.mkdir(parents=True, exist_ok=True)
                computer_id_file.write_text(comp.id)
            print(f"Created cloud smoke-test computer: {comp.id}")
            result = comp.run("printf celesto-smoke")
            assert (result.stdout, result.stderr, result.exit_code) == ("celesto-smoke", "", 0)

            events = list(
                comp.run_stream("printf 'stream-out\\n'; printf 'stream-err\\n' >&2; exit 3")
            )
            stdout = "".join(
                event.data
                for event in events
                if isinstance(event, CommandOutputEvent) and event.type == "stdout"
            )
            stderr = "".join(
                event.data
                for event in events
                if isinstance(event, CommandOutputEvent) and event.type == "stderr"
            )
            exits = [event for event in events if isinstance(event, CommandExitEvent)]
            assert (stdout, stderr) == ("stream-out\n", "stream-err\n")
            assert len(exits) == 1 and exits[0].exit_code == 3

            attached = Computer.get(comp.id)
            assert attached.id == comp.id
            result = attached.run("printf celesto-reconnected")
            assert (result.stdout, result.stderr, result.exit_code) == (
                "celesto-reconnected",
                "",
                0,
            )

            # Serve only the smoke-test file, never the computer's working directory.
            result = comp.run(
                "set -e\n"
                "probe_dir=$(mktemp -d)\n"
                'printf celesto-port-smoke > "$probe_dir/probe.txt"\n'
                "nohup python3 -m http.server 18080 --bind 0.0.0.0 "
                '--directory "$probe_dir" </dev/null >/tmp/celesto-port-smoke.log 2>&1 &'
            )
            assert result.exit_code == 0
            route = comp.publish_port(18080)
            assert isinstance(route, PublishedPort)
            assert route.computer_id == comp.id and route.port == 18080
            assert route.status == "published" and route.url
            assert_public_application(route.url)
            routes = attached.published_ports()
            assert any(r.port == 18080 and r.url == route.url for r in routes)
            assert attached.unpublish_port(18080).status == "unpublished"
            assert all(r.port != 18080 for r in comp.published_ports())
            assert comp.unpublish_port(18080).status == "unpublished"

        with pytest.raises(VMNotFoundError):
            Computer.get(comp.id)
        if computer_id_file is not None:
            computer_id_file.unlink(missing_ok=True)
        print(f"Confirmed cloud smoke-test computer deleted: {comp.id}")
    finally:
        # Retry cleanup if context entry/exit or an assertion failed.
        # Never retry creation, and never hide a failed deletion.
        comp.delete()
        if attached is not None:
            attached.delete()
