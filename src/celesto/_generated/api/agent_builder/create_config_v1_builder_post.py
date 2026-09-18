from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.agent_builder_create_request import AgentBuilderCreateRequest
from ...models.agent_builder_response import AgentBuilderResponse
from ...models.http_validation_error import HTTPValidationError
from typing import cast


def _get_kwargs(
    *,
    body: AgentBuilderCreateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/builder",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AgentBuilderResponse | HTTPValidationError | None:
    if response.status_code == 201:
        response_201 = AgentBuilderResponse.from_dict(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[AgentBuilderResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AgentBuilderCreateRequest,
) -> Response[AgentBuilderResponse | HTTPValidationError]:
    """Create a new agent config

     Create a new agent config.

    Args:
        body (AgentBuilderCreateRequest): Request schema for creating a new agent builder

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentBuilderResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: AgentBuilderCreateRequest,
) -> AgentBuilderResponse | HTTPValidationError | None:
    """Create a new agent config

     Create a new agent config.

    Args:
        body (AgentBuilderCreateRequest): Request schema for creating a new agent builder

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentBuilderResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AgentBuilderCreateRequest,
) -> Response[AgentBuilderResponse | HTTPValidationError]:
    """Create a new agent config

     Create a new agent config.

    Args:
        body (AgentBuilderCreateRequest): Request schema for creating a new agent builder

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentBuilderResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: AgentBuilderCreateRequest,
) -> AgentBuilderResponse | HTTPValidationError | None:
    """Create a new agent config

     Create a new agent config.

    Args:
        body (AgentBuilderCreateRequest): Request schema for creating a new agent builder

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentBuilderResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
