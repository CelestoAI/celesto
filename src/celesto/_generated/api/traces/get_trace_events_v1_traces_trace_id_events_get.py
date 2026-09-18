from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.trace_events_response import TraceEventsResponse
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
        "url": "/v1/traces/{trace_id}/events".format(
            trace_id=quote(str(trace_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TraceEventsResponse | None:
    if response.status_code == 200:
        response_200 = TraceEventsResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TraceEventsResponse]:
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
) -> Response[HTTPValidationError | TraceEventsResponse]:
    """Get trace events for UI

     Get materialized events for a trace.

    Primary data source for tree + waterfall UI rendering.
    Returns a flat list of events with seq/depth for tree positioning
    and start_ms/dur_ms for timeline rendering.

    Args:
        trace_id (str):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TraceEventsResponse]
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
) -> HTTPValidationError | TraceEventsResponse | None:
    """Get trace events for UI

     Get materialized events for a trace.

    Primary data source for tree + waterfall UI rendering.
    Returns a flat list of events with seq/depth for tree positioning
    and start_ms/dur_ms for timeline rendering.

    Args:
        trace_id (str):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TraceEventsResponse
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
) -> Response[HTTPValidationError | TraceEventsResponse]:
    """Get trace events for UI

     Get materialized events for a trace.

    Primary data source for tree + waterfall UI rendering.
    Returns a flat list of events with seq/depth for tree positioning
    and start_ms/dur_ms for timeline rendering.

    Args:
        trace_id (str):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TraceEventsResponse]
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
) -> HTTPValidationError | TraceEventsResponse | None:
    """Get trace events for UI

     Get materialized events for a trace.

    Primary data source for tree + waterfall UI rendering.
    Returns a flat list of events with seq/depth for tree positioning
    and start_ms/dur_ms for timeline rendering.

    Args:
        trace_id (str):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TraceEventsResponse
    """

    return (
        await asyncio_detailed(
            trace_id=trace_id,
            client=client,
            x_current_organization=x_current_organization,
        )
    ).parsed
