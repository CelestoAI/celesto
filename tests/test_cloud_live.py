"""Opt-in smoke test that creates one billable Celesto Cloud computer."""

import os
from pathlib import Path

import pytest

from celesto import CommandExitEvent, CommandOutputEvent, Computer, VMNotFoundError


@pytest.mark.skipif(
    os.getenv("CELESTO_LIVE_TEST") != "1",
    reason="Set CELESTO_LIVE_TEST=1 to create a billable cloud computer.",
)
def test_cloud_live_lifecycle():
    if not os.getenv("CELESTO_API_KEY"):
        pytest.fail("Set CELESTO_API_KEY before running the live cloud test.")

    check_connections = os.getenv("CELESTO_LIVE_CONNECTION_TEST") == "1"
    if check_connections:
        pytest.importorskip("playwright.sync_api")
        pytest.importorskip("websockets.sync.client")
    comp = Computer(**({"template_id": "browser-agent"} if check_connections else {}))
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
            if check_connections:
                _check_connections(comp)

            attached = Computer.get(comp.id)
            assert attached.id == comp.id
            if check_connections:
                _check_connections(attached)
            result = attached.run("printf celesto-reconnected")
            assert (result.stdout, result.stderr, result.exit_code) == (
                "celesto-reconnected",
                "",
                0,
            )

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


def _check_connections(comp):
    from datetime import UTC, datetime

    from playwright.sync_api import sync_playwright
    from websockets.sync.client import connect

    browser_info = comp.browser()
    assert browser_info.expires_at > datetime.now(UTC)
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(browser_info.url)
        try:
            page = browser.contexts[0].new_page()
            page.goto("data:text/html,<title>celesto-connection-smoke</title>")
            assert page.title() == "celesto-connection-smoke"
            refreshed = comp.browser()
            assert refreshed.url != browser_info.url
            assert page.title() == "celesto-connection-smoke"
            page.close()
        finally:
            browser.close()
    for mode in ("read_only", "read_write"):
        display = comp.display(mode=mode)
        assert display.mode == mode and display.expires_at > datetime.now(UTC)
        with connect(display.url, proxy=None, open_timeout=15) as ws:
            assert ws.recv(timeout=15).startswith(b"RFB ")
