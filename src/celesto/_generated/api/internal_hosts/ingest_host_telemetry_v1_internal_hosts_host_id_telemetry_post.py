from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.host_telemetry_request import HostTelemetryRequest
from ...models.host_telemetry_response import HostTelemetryResponse
from ...models.http_validation_error import HTTPValidationError
from typing import cast


def _get_kwargs(
    host_id: str,
    *,
    body: HostTelemetryRequest,
    x_agent_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-agent-key"] = x_agent_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/internal/hosts/{host_id}/telemetry".format(
            host_id=quote(str(host_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | HostTelemetryResponse | None:
    if response.status_code == 200:
        response_200 = HostTelemetryResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | HostTelemetryResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: HostTelemetryRequest,
    x_agent_key: str,
) -> Response[HTTPValidationError | HostTelemetryResponse]:
    """Host agent telemetry batch

    Args:
        host_id (str):
        x_agent_key (str): Host agent shared secret
        body (HostTelemetryRequest): Telemetry batch from a host agent.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | HostTelemetryResponse]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        body=body,
        x_agent_key=x_agent_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: HostTelemetryRequest,
    x_agent_key: str,
) -> HTTPValidationError | HostTelemetryResponse | None:
    """Host agent telemetry batch

    Args:
        host_id (str):
        x_agent_key (str): Host agent shared secret
        body (HostTelemetryRequest): Telemetry batch from a host agent.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | HostTelemetryResponse
    """

    return sync_detailed(
        host_id=host_id,
        client=client,
        body=body,
        x_agent_key=x_agent_key,
    ).parsed


async def asyncio_detailed(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: HostTelemetryRequest,
    x_agent_key: str,
) -> Response[HTTPValidationError | HostTelemetryResponse]:
    """Host agent telemetry batch

    Args:
        host_id (str):
        x_agent_key (str): Host agent shared secret
        body (HostTelemetryRequest): Telemetry batch from a host agent.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | HostTelemetryResponse]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        body=body,
        x_agent_key=x_agent_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: HostTelemetryRequest,
    x_agent_key: str,
) -> HTTPValidationError | HostTelemetryResponse | None:
    """Host agent telemetry batch

    Args:
        host_id (str):
        x_agent_key (str): Host agent shared secret
        body (HostTelemetryRequest): Telemetry batch from a host agent.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | HostTelemetryResponse
    """

    return (
        await asyncio_detailed(
            host_id=host_id,
            client=client,
            body=body,
            x_agent_key=x_agent_key,
        )
    ).parsed
