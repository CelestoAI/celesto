"""The bundled HTTP client must parse both server success shapes.

Risks: a pending invitation is parsed as a member (missing user_id), a member
is mistaken for an invitation, or sync and async wrappers expose different types.
No existing test exercises the generated member endpoint's wire response.
"""

import httpx
import pytest

from _celesto_cloud_api.api.organization_members import (
    add_member_v1_organizations_org_id_members_post as endpoint,
)
from _celesto_cloud_api.client import Client
from _celesto_cloud_api.models.add_member_request import AddMemberRequest


@pytest.mark.parametrize("kind", ["invitation", "active_member", "pending_member"])
@pytest.mark.asyncio
async def test_member_response_union_over_http(kind, tmp_path):
    pending = kind == "invitation"
    payload = (
        {"email": "invite@example.com", "status": "PENDING"}
        if pending
        else {
            "user_id": "member",
            "first_name": "Member",
            "email": "invite@example.com",
            "role": "ADMIN",
            "status": "PENDING" if kind == "pending_member" else "ACTIVE",
            "joined_at": "2026-11-03T12:00:00Z",
        }
    )
    transport = httpx.MockTransport(lambda request: httpx.Response(201, json=payload))
    client = Client(base_url="https://test")
    body = AddMemberRequest(email=payload["email"])
    with httpx.Client(transport=transport, base_url="https://test") as http:
        client.set_httpx_client(http)
        result = endpoint.sync("org", client=client, body=body)
    async with httpx.AsyncClient(transport=transport, base_url="https://test") as http:
        client.set_async_httpx_client(http)
        async_result = await endpoint.asyncio("org", client=client, body=body)
    assert type(result).__name__ == ("InvitationRead" if pending else "OrganizationMemberRead")
    assert type(async_result) is type(result)
    assert result.to_dict()["email"] == payload["email"]
    assert result.to_dict()["status"] == payload["status"]
    tmp_path.joinpath("response.json").write_text(
        __import__("json").dumps(result.to_dict(), default=str)
    )
