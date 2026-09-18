from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.project_list_response import ProjectListResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    skip: int | Unset = 0,
    limit: int | Unset = 50,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    params: dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/projects/",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ProjectListResponse | None:
    if response.status_code == 200:
        response_200 = ProjectListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | ProjectListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = 0,
    limit: int | Unset = 50,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | ProjectListResponse]:
    """List projects in organization

     Lists all projects in the current organization with pagination.

    Args:
        skip (int | Unset): Number of items to skip Default: 0.
        limit (int | Unset): Maximum items to return Default: 50.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ProjectListResponse]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = 0,
    limit: int | Unset = 50,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | ProjectListResponse | None:
    """List projects in organization

     Lists all projects in the current organization with pagination.

    Args:
        skip (int | Unset): Number of items to skip Default: 0.
        limit (int | Unset): Maximum items to return Default: 50.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ProjectListResponse
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = 0,
    limit: int | Unset = 50,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | ProjectListResponse]:
    """List projects in organization

     Lists all projects in the current organization with pagination.

    Args:
        skip (int | Unset): Number of items to skip Default: 0.
        limit (int | Unset): Maximum items to return Default: 50.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ProjectListResponse]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = 0,
    limit: int | Unset = 50,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | ProjectListResponse | None:
    """List projects in organization

     Lists all projects in the current organization with pagination.

    Args:
        skip (int | Unset): Number of items to skip Default: 0.
        limit (int | Unset): Maximum items to return Default: 50.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ProjectListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            x_current_organization=x_current_organization,
        )
    ).parsed
