from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.trace_bulk_delete_request import TraceBulkDeleteRequest
from ...models.trace_bulk_delete_response import TraceBulkDeleteResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    body: TraceBulkDeleteRequest,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/traces/bulk-delete",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TraceBulkDeleteResponse | None:
    if response.status_code == 200:
        response_200 = TraceBulkDeleteResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TraceBulkDeleteResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TraceBulkDeleteRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | TraceBulkDeleteResponse]:
    """Delete multiple traces

     Delete multiple traces and all associated spans and events.

    Only deletes traces that exist and belong to the organization.
    Returns the count of traces actually deleted.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (TraceBulkDeleteRequest): Request body for bulk trace deletion.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TraceBulkDeleteResponse]
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
    body: TraceBulkDeleteRequest,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | TraceBulkDeleteResponse | None:
    """Delete multiple traces

     Delete multiple traces and all associated spans and events.

    Only deletes traces that exist and belong to the organization.
    Returns the count of traces actually deleted.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (TraceBulkDeleteRequest): Request body for bulk trace deletion.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TraceBulkDeleteResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TraceBulkDeleteRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | TraceBulkDeleteResponse]:
    """Delete multiple traces

     Delete multiple traces and all associated spans and events.

    Only deletes traces that exist and belong to the organization.
    Returns the count of traces actually deleted.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (TraceBulkDeleteRequest): Request body for bulk trace deletion.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TraceBulkDeleteResponse]
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
    body: TraceBulkDeleteRequest,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | TraceBulkDeleteResponse | None:
    """Delete multiple traces

     Delete multiple traces and all associated spans and events.

    Only deletes traces that exist and belong to the organization.
    Returns the count of traces actually deleted.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (TraceBulkDeleteRequest): Request body for bulk trace deletion.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TraceBulkDeleteResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_current_organization=x_current_organization,
        )
    ).parsed
