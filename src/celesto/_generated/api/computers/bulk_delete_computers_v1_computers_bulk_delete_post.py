from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.computer_bulk_delete_request import ComputerBulkDeleteRequest
from ...models.computer_bulk_delete_response import ComputerBulkDeleteResponse
from ...models.computer_validation_error_response import ComputerValidationErrorResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    body: ComputerBulkDeleteRequest,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/computers/bulk-delete",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ComputerBulkDeleteResponse | ComputerValidationErrorResponse | None:
    if response.status_code == 200:
        response_200 = ComputerBulkDeleteResponse.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = ComputerValidationErrorResponse.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ComputerBulkDeleteResponse | ComputerValidationErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ComputerBulkDeleteRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[ComputerBulkDeleteResponse | ComputerValidationErrorResponse]:
    """Delete multiple computers

     Delete multiple computers in a single best-effort request.

    Each ID is deleted independently via the same path as single delete, so
    a single bad ID (not found, already deleted, host error) does not abort
    the rest of the batch. Returns the IDs that were deleted and the IDs
    that failed.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (ComputerBulkDeleteRequest): Request body for deleting multiple computers.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ComputerBulkDeleteResponse | ComputerValidationErrorResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: ComputerBulkDeleteRequest,
    x_current_organization: str | Unset = UNSET,
) -> ComputerBulkDeleteResponse | ComputerValidationErrorResponse | None:
    """Delete multiple computers

     Delete multiple computers in a single best-effort request.

    Each ID is deleted independently via the same path as single delete, so
    a single bad ID (not found, already deleted, host error) does not abort
    the rest of the batch. Returns the IDs that were deleted and the IDs
    that failed.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (ComputerBulkDeleteRequest): Request body for deleting multiple computers.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ComputerBulkDeleteResponse | ComputerValidationErrorResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ComputerBulkDeleteRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[ComputerBulkDeleteResponse | ComputerValidationErrorResponse]:
    """Delete multiple computers

     Delete multiple computers in a single best-effort request.

    Each ID is deleted independently via the same path as single delete, so
    a single bad ID (not found, already deleted, host error) does not abort
    the rest of the batch. Returns the IDs that were deleted and the IDs
    that failed.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (ComputerBulkDeleteRequest): Request body for deleting multiple computers.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ComputerBulkDeleteResponse | ComputerValidationErrorResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: ComputerBulkDeleteRequest,
    x_current_organization: str | Unset = UNSET,
) -> ComputerBulkDeleteResponse | ComputerValidationErrorResponse | None:
    """Delete multiple computers

     Delete multiple computers in a single best-effort request.

    Each ID is deleted independently via the same path as single delete, so
    a single bad ID (not found, already deleted, host error) does not abort
    the rest of the batch. Returns the IDs that were deleted and the IDs
    that failed.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (ComputerBulkDeleteRequest): Request body for deleting multiple computers.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ComputerBulkDeleteResponse | ComputerValidationErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_current_organization=x_current_organization,
        )
    ).parsed
