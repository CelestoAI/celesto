"""The review example uses the SDK lifecycle, not the old dictionary API."""

import runpy
from pathlib import Path
from unittest.mock import Mock

import pytest

from celesto.exceptions import CelestoError


@pytest.mark.parametrize(
    "failure", [None, CelestoError("startup failed"), TimeoutError("timed out")]
)
def test_cloud_example_starts_through_sdk(monkeypatch, failure):
    from celesto import CloudComputer

    sandbox_class = runpy.run_path(
        str(Path(__file__).parents[1] / "examples/pr-review-jev/sandboxes.py")
    )["Sandbox"]
    adapter = Mock()
    adapter.start.side_effect = failure
    provider_factory = Mock(return_value=adapter)
    monkeypatch.setattr("celesto.sdk.make_provider", provider_factory)
    monkeypatch.setenv("CELESTO_TEMPLATE", "coding-agent")
    # Keep the real lifecycle implementation and forbid old status polling.
    monkeypatch.setattr(CloudComputer, "get", Mock(side_effect=AssertionError("not status lookup")))
    if failure is None:
        sandbox = sandbox_class("cloud")
        assert isinstance(sandbox.vm, CloudComputer)
        adapter.delete.assert_not_called()
    else:
        with pytest.raises(type(failure)) as caught:
            sandbox_class("cloud")
        assert caught.value is failure
        adapter.delete.assert_called_once()
        adapter.close.assert_called_once()
    adapter.start.assert_called_once()
    provider_factory.assert_called_once_with(
        "cloud", {"template_id": "coding-agent", "startup_timeout": 180}
    )
