from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.trace_detail_response import TraceDetailResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    trace_id: str,
    *,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/traces/{trace_id}".format(
            trace_id=quote(str(trace_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TraceDetailResponse | None:
    if response.status_code == 200:
        response_200 = TraceDetailResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TraceDetailResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    trace_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | TraceDetailResponse]:
    """Get trace details

     Get detailed trace metadata with aggregated stats.

    Returns trace metadata, timing information, and computed statistics
    including token usage, tool calls count, and error count.

    Args:
        trace_id (str):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TraceDetailResponse]
    """

    kwargs = _get_kwargs(
        trace_id=trace_id,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    trace_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | TraceDetailResponse | None:
    """Get trace details

     Get detailed trace metadata with aggregated stats.

    Returns trace metadata, timing information, and computed statistics
    including token usage, tool calls count, and error count.

    Args:
        trace_id (str):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TraceDetailResponse
    """

    return sync_detailed(
        trace_id=trace_id,
        client=client,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    trace_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | TraceDetailResponse]:
    """Get trace details

     Get detailed trace metadata with aggregated stats.

    Returns trace metadata, timing information, and computed statistics
    including token usage, tool calls count, and error count.

    Args:
        trace_id (str):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TraceDetailResponse]
    """

    kwargs = _get_kwargs(
        trace_id=trace_id,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    trace_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | TraceDetailResponse | None:
    """Get trace details

     Get detailed trace metadata with aggregated stats.

    Returns trace metadata, timing information, and computed statistics
    including token usage, tool calls count, and error count.

    Args:
        trace_id (str):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TraceDetailResponse
    """

    return (
        await asyncio_detailed(
            trace_id=trace_id,
            client=client,
            x_current_organization=x_current_organization,
        )
    ).parsed
