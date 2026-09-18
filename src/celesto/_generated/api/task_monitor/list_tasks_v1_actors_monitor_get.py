from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.status import Status
from ...models.task_monitor_list_response import TaskMonitorListResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    page: int | Unset = 1,
    page_size: int | Unset = 50,
    status: None | Status | Unset = UNSET,
    task_type: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    params: dict[str, Any] = {}

    params["page"] = page

    params["page_size"] = page_size

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, Status):
        json_status = status.value
    else:
        json_status = status
    params["status"] = json_status

    json_task_type: None | str | Unset
    if isinstance(task_type, Unset):
        json_task_type = UNSET
    else:
        json_task_type = task_type
    params["task_type"] = json_task_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/actors/monitor",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TaskMonitorListResponse | None:
    if response.status_code == 200:
        response_200 = TaskMonitorListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TaskMonitorListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    page_size: int | Unset = 50,
    status: None | Status | Unset = UNSET,
    task_type: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | TaskMonitorListResponse]:
    """List task monitor records

     List actors for the current organization with pagination.

    Args:
        page (int | Unset): Page number starting at 1 Default: 1.
        page_size (int | Unset): Number of actors per page Default: 50.
        status (None | Status | Unset):
        task_type (None | str | Unset):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TaskMonitorListResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        status=status,
        task_type=task_type,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    page_size: int | Unset = 50,
    status: None | Status | Unset = UNSET,
    task_type: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | TaskMonitorListResponse | None:
    """List task monitor records

     List actors for the current organization with pagination.

    Args:
        page (int | Unset): Page number starting at 1 Default: 1.
        page_size (int | Unset): Number of actors per page Default: 50.
        status (None | Status | Unset):
        task_type (None | str | Unset):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TaskMonitorListResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        page_size=page_size,
        status=status,
        task_type=task_type,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    page_size: int | Unset = 50,
    status: None | Status | Unset = UNSET,
    task_type: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | TaskMonitorListResponse]:
    """List task monitor records

     List actors for the current organization with pagination.

    Args:
        page (int | Unset): Page number starting at 1 Default: 1.
        page_size (int | Unset): Number of actors per page Default: 50.
        status (None | Status | Unset):
        task_type (None | str | Unset):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TaskMonitorListResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        status=status,
        task_type=task_type,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    page_size: int | Unset = 50,
    status: None | Status | Unset = UNSET,
    task_type: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | TaskMonitorListResponse | None:
    """List task monitor records

     List actors for the current organization with pagination.

    Args:
        page (int | Unset): Page number starting at 1 Default: 1.
        page_size (int | Unset): Number of actors per page Default: 50.
        status (None | Status | Unset):
        task_type (None | str | Unset):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TaskMonitorListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            page_size=page_size,
            status=status,
            task_type=task_type,
            x_current_organization=x_current_organization,
        )
    ).parsed
