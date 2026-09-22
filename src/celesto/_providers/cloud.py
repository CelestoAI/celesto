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


def get_cloud_computer(computer_id: str) -> dict[str, str | int]:
    """Return public CLI fields for one cloud computer without leaking generated models."""
    from _celesto_cloud_api.api.computers import get_computer_v1_computers_computer_id_get
    from _celesto_cloud_api.models.computer_response import ComputerResponse

    provider = CloudProvider()
    provider.vm_id = computer_id
    try:
        computer = provider._call(
            get_computer_v1_computers_computer_id_get.sync_detailed,
            ComputerResponse,
            computer_id=computer_id,
        )
        return {
            "computer_id": computer.id,
            "name": computer.name,
            "status": computer.status,
            "vcpus": computer.vcpus,
            "ram_mb": computer.ram_mb,
            "disk_size_mb": computer.disk_size_mb,
            "image": computer.image,
            "created_at": computer.created_at,
        }
    finally:
        provider.close()


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
