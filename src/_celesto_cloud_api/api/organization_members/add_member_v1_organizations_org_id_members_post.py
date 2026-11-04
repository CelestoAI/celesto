from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.add_member_request import AddMemberRequest
from ...models.http_validation_error import HTTPValidationError
from ...models.invitation_read import InvitationRead
from ...models.organization_member_read import OrganizationMemberRead
from typing import cast


def _get_kwargs(
    org_id: str,
    *,
    body: AddMemberRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/organizations/{org_id}/members/".format(
            org_id=quote(str(org_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | InvitationRead | OrganizationMemberRead | None:
    if response.status_code == 201:

        def _parse_response_201(
            data: object,
        ) -> InvitationRead | OrganizationMemberRead:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_201_type_0 = OrganizationMemberRead.from_dict(data)

                return response_201_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_201_type_1 = InvitationRead.from_dict(data)

            return response_201_type_1

        response_201 = _parse_response_201(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | InvitationRead | OrganizationMemberRead]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: AddMemberRequest,
) -> Response[HTTPValidationError | InvitationRead | OrganizationMemberRead]:
    """Add a member to the organization

     Adds a user to the organization with the specified role. Reactivates if previously removed.

    Args:
        org_id (str): The ID of the organization
        body (AddMemberRequest): Schema for adding a user to an organization.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | InvitationRead | OrganizationMemberRead]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: AddMemberRequest,
) -> HTTPValidationError | InvitationRead | OrganizationMemberRead | None:
    """Add a member to the organization

     Adds a user to the organization with the specified role. Reactivates if previously removed.

    Args:
        org_id (str): The ID of the organization
        body (AddMemberRequest): Schema for adding a user to an organization.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | InvitationRead | OrganizationMemberRead
    """

    return sync_detailed(
        org_id=org_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: AddMemberRequest,
) -> Response[HTTPValidationError | InvitationRead | OrganizationMemberRead]:
    """Add a member to the organization

     Adds a user to the organization with the specified role. Reactivates if previously removed.

    Args:
        org_id (str): The ID of the organization
        body (AddMemberRequest): Schema for adding a user to an organization.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | InvitationRead | OrganizationMemberRead]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: AddMemberRequest,
) -> HTTPValidationError | InvitationRead | OrganizationMemberRead | None:
    """Add a member to the organization

     Adds a user to the organization with the specified role. Reactivates if previously removed.

    Args:
        org_id (str): The ID of the organization
        body (AddMemberRequest): Schema for adding a user to an organization.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | InvitationRead | OrganizationMemberRead
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            client=client,
            body=body,
        )
    ).parsed
