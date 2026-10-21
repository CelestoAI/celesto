"""Opt-in smoke test that builds one custom template and boots a billable computer from it."""

import contextlib
import os
import time

import pytest

from celesto import CloudAPIError, Template


@pytest.mark.skipif(
    os.getenv("CELESTO_LIVE_TEMPLATE_TEST") != "1",
    reason="Set CELESTO_LIVE_TEMPLATE_TEST=1 to build a template and create a billable computer.",
)
def test_template_live_build_and_boot():
    if not os.getenv("CELESTO_API_KEY"):
        pytest.fail("Set CELESTO_API_KEY before running the live template test.")

    marker = f"celesto-template-smoke-{int(time.time())}"
    warnings = Template.lint("apt-get install cowsay")
    assert [w.code for w in warnings] == ["apt_without_yes"]

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
        with contextlib.suppress(CloudAPIError):
            template.delete()
        template.close()
