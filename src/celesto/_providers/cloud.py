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
