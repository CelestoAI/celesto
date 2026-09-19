"""Opt-in smoke test that creates one billable Celesto Cloud computer."""

import os
from pathlib import Path

import pytest

from celesto import Computer, VMNotFoundError


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

            attached = Computer.get(comp.id)
            assert attached.id == comp.id
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
