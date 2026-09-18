from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.add_member_request import AddMemberRequest
from ...models.http_validation_error import HTTPValidationError
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
) -> HTTPValidationError | OrganizationMemberRead | None:
    if response.status_code == 201:
        response_201 = OrganizationMemberRead.from_dict(response.json())

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
) -> Response[HTTPValidationError | OrganizationMemberRead]:
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
) -> Response[HTTPValidationError | OrganizationMemberRead]:
    """Add a member to the organization

     Adds a user to the organization with the specified role. Reactivates if previously removed.

    Args:
        org_id (str): The ID of the organization
        body (AddMemberRequest): Schema for adding a user to an organization.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OrganizationMemberRead]
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
) -> HTTPValidationError | OrganizationMemberRead | None:
    """Add a member to the organization

     Adds a user to the organization with the specified role. Reactivates if previously removed.

    Args:
        org_id (str): The ID of the organization
        body (AddMemberRequest): Schema for adding a user to an organization.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OrganizationMemberRead
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
) -> Response[HTTPValidationError | OrganizationMemberRead]:
    """Add a member to the organization

     Adds a user to the organization with the specified role. Reactivates if previously removed.

    Args:
        org_id (str): The ID of the organization
        body (AddMemberRequest): Schema for adding a user to an organization.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OrganizationMemberRead]
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
) -> HTTPValidationError | OrganizationMemberRead | None:
    """Add a member to the organization

     Adds a user to the organization with the specified role. Reactivates if previously removed.

    Args:
        org_id (str): The ID of the organization
        body (AddMemberRequest): Schema for adding a user to an organization.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OrganizationMemberRead
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            client=client,
            body=body,
        )
    ).parsed
