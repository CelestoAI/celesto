from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.trace_ingest_payload import TraceIngestPayload
from ...models.trace_ingest_response import TraceIngestResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    body: TraceIngestPayload,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/traces/ingest",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TraceIngestResponse | None:
    if response.status_code == 202:
        response_202 = TraceIngestResponse.from_dict(response.json())

        return response_202

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | TraceIngestResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TraceIngestPayload,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | TraceIngestResponse]:
    """Ingest trace and span data

     Ingest trace and span data from OpenAI Agents SDK.

    Accepts a batch of items where each item has an 'object' field
    indicating whether it's a 'trace' or 'trace.span'.

    Items are upserted to the database and materialization is
    automatically enqueued for affected traces.

    Returns:
        TraceIngestResponse with count of accepted items and trace IDs

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (TraceIngestPayload): Request body for trace ingestion endpoint.

            Accepts a list of items where each item has an 'object' field
            indicating whether it's a 'trace' or 'trace.span'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TraceIngestResponse]
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
    body: TraceIngestPayload,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | TraceIngestResponse | None:
    """Ingest trace and span data

     Ingest trace and span data from OpenAI Agents SDK.

    Accepts a batch of items where each item has an 'object' field
    indicating whether it's a 'trace' or 'trace.span'.

    Items are upserted to the database and materialization is
    automatically enqueued for affected traces.

    Returns:
        TraceIngestResponse with count of accepted items and trace IDs

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (TraceIngestPayload): Request body for trace ingestion endpoint.

            Accepts a list of items where each item has an 'object' field
            indicating whether it's a 'trace' or 'trace.span'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TraceIngestResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TraceIngestPayload,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | TraceIngestResponse]:
    """Ingest trace and span data

     Ingest trace and span data from OpenAI Agents SDK.

    Accepts a batch of items where each item has an 'object' field
    indicating whether it's a 'trace' or 'trace.span'.

    Items are upserted to the database and materialization is
    automatically enqueued for affected traces.

    Returns:
        TraceIngestResponse with count of accepted items and trace IDs

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (TraceIngestPayload): Request body for trace ingestion endpoint.

            Accepts a list of items where each item has an 'object' field
            indicating whether it's a 'trace' or 'trace.span'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TraceIngestResponse]
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
    body: TraceIngestPayload,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | TraceIngestResponse | None:
    """Ingest trace and span data

     Ingest trace and span data from OpenAI Agents SDK.

    Accepts a batch of items where each item has an 'object' field
    indicating whether it's a 'trace' or 'trace.span'.

    Items are upserted to the database and materialization is
    automatically enqueued for affected traces.

    Returns:
        TraceIngestResponse with count of accepted items and trace IDs

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (TraceIngestPayload): Request body for trace ingestion endpoint.

            Accepts a list of items where each item has an 'object' field
            indicating whether it's a 'trace' or 'trace.span'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TraceIngestResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_current_organization=x_current_organization,
        )
    ).parsed
