from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.host_register_request import HostRegisterRequest
from ...models.host_response import HostResponse
from ...models.http_validation_error import HTTPValidationError
from typing import cast


def _get_kwargs(
    *,
    body: HostRegisterRequest,
    x_agent_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-agent-key"] = x_agent_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/internal/hosts/register",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | HostResponse | None:
    if response.status_code == 200:
        response_200 = HostResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | HostResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: HostRegisterRequest,
    x_agent_key: str,
) -> Response[HTTPValidationError | HostResponse]:
    """Register or update a compute host

    Args:
        x_agent_key (str): Host agent shared secret
        body (HostRegisterRequest): Request from a host agent to register itself.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | HostResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        x_agent_key=x_agent_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: HostRegisterRequest,
    x_agent_key: str,
) -> HTTPValidationError | HostResponse | None:
    """Register or update a compute host

    Args:
        x_agent_key (str): Host agent shared secret
        body (HostRegisterRequest): Request from a host agent to register itself.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | HostResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        x_agent_key=x_agent_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: HostRegisterRequest,
    x_agent_key: str,
) -> Response[HTTPValidationError | HostResponse]:
    """Register or update a compute host

    Args:
        x_agent_key (str): Host agent shared secret
        body (HostRegisterRequest): Request from a host agent to register itself.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | HostResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        x_agent_key=x_agent_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: HostRegisterRequest,
    x_agent_key: str,
) -> HTTPValidationError | HostResponse | None:
    """Register or update a compute host

    Args:
        x_agent_key (str): Host agent shared secret
        body (HostRegisterRequest): Request from a host agent to register itself.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | HostResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_agent_key=x_agent_key,
        )
    ).parsed
