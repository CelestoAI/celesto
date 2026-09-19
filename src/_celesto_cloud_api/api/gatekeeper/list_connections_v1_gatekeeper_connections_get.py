from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.delegated_access_list_response import DelegatedAccessListResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    project_name: str,
    status_filter: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    params: dict[str, Any] = {}

    params["project_name"] = project_name

    json_status_filter: None | str | Unset
    if isinstance(status_filter, Unset):
        json_status_filter = UNSET
    else:
        json_status_filter = status_filter
    params["status_filter"] = json_status_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/gatekeeper/connections",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DelegatedAccessListResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DelegatedAccessListResponse.from_dict(response.json())

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
) -> Response[DelegatedAccessListResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_name: str,
    status_filter: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[DelegatedAccessListResponse | HTTPValidationError]:
    """List Connections

     List all delegated access connections for a project

    Args:
        project_name (str): Project name to list connections for
        status_filter (None | str | Unset): Filter by status (ACTIVE, REVOKED, PENDING)
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DelegatedAccessListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        project_name=project_name,
        status_filter=status_filter,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    project_name: str,
    status_filter: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> DelegatedAccessListResponse | HTTPValidationError | None:
    """List Connections

     List all delegated access connections for a project

    Args:
        project_name (str): Project name to list connections for
        status_filter (None | str | Unset): Filter by status (ACTIVE, REVOKED, PENDING)
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DelegatedAccessListResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        project_name=project_name,
        status_filter=status_filter,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_name: str,
    status_filter: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[DelegatedAccessListResponse | HTTPValidationError]:
    """List Connections

     List all delegated access connections for a project

    Args:
        project_name (str): Project name to list connections for
        status_filter (None | str | Unset): Filter by status (ACTIVE, REVOKED, PENDING)
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DelegatedAccessListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        project_name=project_name,
        status_filter=status_filter,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    project_name: str,
    status_filter: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> DelegatedAccessListResponse | HTTPValidationError | None:
    """List Connections

     List all delegated access connections for a project

    Args:
        project_name (str): Project name to list connections for
        status_filter (None | str | Unset): Filter by status (ACTIVE, REVOKED, PENDING)
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DelegatedAccessListResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            project_name=project_name,
            status_filter=status_filter,
            x_current_organization=x_current_organization,
        )
    ).parsed
