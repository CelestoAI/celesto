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


def stop_cloud_computer(computer_id: str) -> dict[str, str]:
    """Pause a cloud computer and return its public CLI fields."""
    from _celesto_cloud_api.api.computers import stop_computer_v1_computers_computer_id_stop_post
    from _celesto_cloud_api.models.computer_response import ComputerResponse

    provider = CloudProvider()
    provider.vm_id = computer_id
    try:
        computer = provider._call(
            stop_computer_v1_computers_computer_id_stop_post.sync_detailed,
            ComputerResponse,
            uncertain_mutation=f"stop computer {computer_id}",
            computer_id=computer_id,
        )
        return {"computer_id": computer.id, "status": computer.status}
    finally:
        provider.close()


def start_cloud_computer(computer_id: str) -> dict[str, str]:
    """Resume a paused cloud computer and return its public CLI fields."""
    from _celesto_cloud_api.api.computers import start_computer_v1_computers_computer_id_start_post
    from _celesto_cloud_api.models.computer_response import ComputerResponse

    provider = CloudProvider()
    provider.vm_id = computer_id
    try:
        computer = provider._call(
            start_computer_v1_computers_computer_id_start_post.sync_detailed,
            ComputerResponse,
            uncertain_mutation=f"start computer {computer_id}",
            computer_id=computer_id,
        )
        return {"computer_id": computer.id, "status": computer.status}
    finally:
        provider.close()


def list_cloud_computers(limit: int = 50) -> tuple[list[dict[str, str]], bool]:
    """Return public CLI fields and flag a potentially incomplete list."""
    from _celesto_cloud_api.api.computers import list_computers_v1_computers_get
    from _celesto_cloud_api.models.computer_list_response import ComputerListResponse

    provider = CloudProvider()
    try:
        response = provider._call(
            list_computers_v1_computers_get.sync_detailed, ComputerListResponse, limit=limit
        )
        rows = [
            {"computer_id": computer.id, "status": computer.status}
            for computer in response.computers
        ]
        # The API exposes a limit but no offset or cursor. A full page may
        # hide more computers even when count describes only this response.
        return rows, len(rows) >= limit or response.count > len(rows)
    finally:
        provider.close()
