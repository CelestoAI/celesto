"""Adapt the cloud transport to the common provider contract."""

from celesto._cloud import _CloudComputer


class CloudProvider(_CloudComputer):
    @property
    def id(self) -> str | None:
        return self.vm_id

    def validate_terminal(self, terminal_id: str | None) -> None:
        pass

    def validate_ports(self) -> None:
        pass


def list_cloud_computers() -> list[dict[str, str]]:
    """Return public CLI fields without leaking generated models."""
    from _celesto_cloud_api.api.computers import list_computers_v1_computers_get
    from _celesto_cloud_api.models.computer_list_response import ComputerListResponse

    provider = CloudProvider()
    try:
        response = provider._call(
            list_computers_v1_computers_get.sync_detailed, ComputerListResponse
        )
        return [
            {"computer_id": computer.id, "status": computer.status}
            for computer in response.computers
        ]
    finally:
        provider.close()
