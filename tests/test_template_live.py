"""Opt-in smoke test that builds one custom template and boots a billable computer from it."""

import contextlib
import json
import os
import time

import pytest

from celesto import CloudAPIError, Template


@pytest.mark.skipif(
    os.getenv("CELESTO_LIVE_TEMPLATE_TEST") != "1",
    reason="Set CELESTO_LIVE_TEMPLATE_TEST=1 to build a template and create a billable computer.",
)
def test_template_live_build_and_boot(tmp_path):
    if not os.getenv("CELESTO_API_KEY"):
        pytest.fail("Set CELESTO_API_KEY before running the live template test.")

    marker = f"celesto-template-smoke-{int(time.time())}"
    warnings = Template.lint("apt-get install cowsay")
    # The API may add lint checks; this one must stay.
    assert "apt_without_yes" in [w.code for w in warnings]

    template = Template.create(
        name=marker,
        build_script=f"echo {marker} > /etc/celesto-template-smoke\n",
    )
    log = []
    try:
        assert template.id.startswith("tpl_")
        assert any(t.id == template.id for t in Template.list())

        template.wait(on_log=log.append)
        assert template.status == "ready"
        assert marker in "".join(log)

        with template.create_computer() as computer:
            result = computer.run("cat /etc/celesto-template-smoke")
        assert result.stdout.strip() == marker
    finally:
        # Keep a record of the run: which template, how it ended, and its log.
        artifact = tmp_path / "template-live-run.json"
        artifact.write_text(
            json.dumps(
                {"template_id": template.id, "status": template.status, "log": "".join(log)},
                indent=2,
            )
        )
        print(f"Live template run recorded at {artifact}")
        with contextlib.suppress(CloudAPIError):
            template.delete()
        template.close()
