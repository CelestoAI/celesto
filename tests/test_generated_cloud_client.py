"""Contract tests that depend only on the generated cloud client."""

from importlib import import_module
from pkgutil import walk_packages

import _celesto_cloud_api
from _celesto_cloud_api import AuthenticatedClient
from _celesto_cloud_api.models.computer_response import ComputerResponse


def test_every_generated_module_imports() -> None:
    modules = list(
        walk_packages(_celesto_cloud_api.__path__, prefix=f"{_celesto_cloud_api.__name__}.")
    )

    assert modules
    for module in modules:
        import_module(module.name)


def test_authenticated_client_adds_bearer_token() -> None:
    client = AuthenticatedClient(
        base_url="https://api.example.test",
        token="test-token",
    )

    with client:
        assert client.get_httpx_client().headers["Authorization"] == "Bearer test-token"


def test_computer_response_round_trips_required_fields() -> None:
    payload = {
        "id": "cmp-test",
        "name": "test-computer",
        "status": "running",
        "vcpus": 2,
        "ram_mb": 2048,
        "disk_size_mb": 10240,
        "image": "ubuntu-desktop-24.04",
        "created_at": "2026-09-19T00:00:00Z",
    }

    computer = ComputerResponse.from_dict(payload)

    assert computer.id == "cmp-test"
    assert computer.to_dict() == payload
