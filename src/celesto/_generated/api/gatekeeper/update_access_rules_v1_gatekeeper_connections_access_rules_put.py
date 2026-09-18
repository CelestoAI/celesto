from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.drive_access_rules_response import DriveAccessRulesResponse
from ...models.drive_access_rules_update import DriveAccessRulesUpdate
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    body: DriveAccessRulesUpdate,
    subject: str,
    project_name: str,
    provider: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    params: dict[str, Any] = {}

    params["subject"] = subject

    params["project_name"] = project_name

    json_provider: None | str | Unset
    if isinstance(provider, Unset):
        json_provider = UNSET
    else:
        json_provider = provider
    params["provider"] = json_provider

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/v1/gatekeeper/connections/access-rules",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DriveAccessRulesResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DriveAccessRulesResponse.from_dict(response.json())

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
) -> Response[DriveAccessRulesResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DriveAccessRulesUpdate,
    subject: str,
    project_name: str,
    provider: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[DriveAccessRulesResponse | HTTPValidationError]:
    """Update Access Rules

     Update access rules for a delegated access connection by subject

    Args:
        subject (str): Subject identifier (e.g., 'user:email@example.com')
        project_name (str): Project name
        provider (None | str | Unset): Provider filter (e.g., 'google_drive')
        x_current_organization (str | Unset): Current organization ID
        body (DriveAccessRulesUpdate): Request to update access rules for a connection.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DriveAccessRulesResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        subject=subject,
        project_name=project_name,
        provider=provider,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: DriveAccessRulesUpdate,
    subject: str,
    project_name: str,
    provider: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> DriveAccessRulesResponse | HTTPValidationError | None:
    """Update Access Rules

     Update access rules for a delegated access connection by subject

    Args:
        subject (str): Subject identifier (e.g., 'user:email@example.com')
        project_name (str): Project name
        provider (None | str | Unset): Provider filter (e.g., 'google_drive')
        x_current_organization (str | Unset): Current organization ID
        body (DriveAccessRulesUpdate): Request to update access rules for a connection.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DriveAccessRulesResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
        subject=subject,
        project_name=project_name,
        provider=provider,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DriveAccessRulesUpdate,
    subject: str,
    project_name: str,
    provider: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[DriveAccessRulesResponse | HTTPValidationError]:
    """Update Access Rules

     Update access rules for a delegated access connection by subject

    Args:
        subject (str): Subject identifier (e.g., 'user:email@example.com')
        project_name (str): Project name
        provider (None | str | Unset): Provider filter (e.g., 'google_drive')
        x_current_organization (str | Unset): Current organization ID
        body (DriveAccessRulesUpdate): Request to update access rules for a connection.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DriveAccessRulesResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        subject=subject,
        project_name=project_name,
        provider=provider,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: DriveAccessRulesUpdate,
    subject: str,
    project_name: str,
    provider: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> DriveAccessRulesResponse | HTTPValidationError | None:
    """Update Access Rules

     Update access rules for a delegated access connection by subject

    Args:
        subject (str): Subject identifier (e.g., 'user:email@example.com')
        project_name (str): Project name
        provider (None | str | Unset): Provider filter (e.g., 'google_drive')
        x_current_organization (str | Unset): Current organization ID
        body (DriveAccessRulesUpdate): Request to update access rules for a connection.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DriveAccessRulesResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            subject=subject,
            project_name=project_name,
            provider=provider,
            x_current_organization=x_current_organization,
        )
    ).parsed
