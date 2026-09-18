from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.organization import Organization
from ...models.organization_update import OrganizationUpdate
from typing import cast


def _get_kwargs(
    org_id: str,
    *,
    body: OrganizationUpdate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/v1/organizations/{org_id}".format(
            org_id=quote(str(org_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | Organization | None:
    if response.status_code == 200:
        response_200 = Organization.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | Organization]:
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
    body: OrganizationUpdate,
) -> Response[HTTPValidationError | Organization]:
    """Update an organization

     Updates an organization's details. Requires admin permissions.

    Args:
        org_id (str): The ID of the organization
        body (OrganizationUpdate): Schema for updating Organization - only name allowed (rename
            feature)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | Organization]
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
    body: OrganizationUpdate,
) -> HTTPValidationError | Organization | None:
    """Update an organization

     Updates an organization's details. Requires admin permissions.

    Args:
        org_id (str): The ID of the organization
        body (OrganizationUpdate): Schema for updating Organization - only name allowed (rename
            feature)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | Organization
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
    body: OrganizationUpdate,
) -> Response[HTTPValidationError | Organization]:
    """Update an organization

     Updates an organization's details. Requires admin permissions.

    Args:
        org_id (str): The ID of the organization
        body (OrganizationUpdate): Schema for updating Organization - only name allowed (rename
            feature)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | Organization]
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
    body: OrganizationUpdate,
) -> HTTPValidationError | Organization | None:
    """Update an organization

     Updates an organization's details. Requires admin permissions.

    Args:
        org_id (str): The ID of the organization
        body (OrganizationUpdate): Schema for updating Organization - only name allowed (rename
            feature)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | Organization
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            client=client,
            body=body,
        )
    ).parsed
