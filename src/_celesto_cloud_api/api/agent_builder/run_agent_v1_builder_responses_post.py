from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.agent_builder_run_request import AgentBuilderRunRequest
from ...models.agent_builder_run_response import AgentBuilderRunResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    body: AgentBuilderRunRequest,
    x_agent_id: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_agent_id, Unset):
        headers["x-agent-id"] = x_agent_id

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/builder/responses",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AgentBuilderRunResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AgentBuilderRunResponse.from_dict(response.json())

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
) -> Response[AgentBuilderRunResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AgentBuilderRunRequest,
    x_agent_id: None | str | Unset = UNSET,
) -> Response[AgentBuilderRunResponse | HTTPValidationError]:
    """Run agent

     Execute an agent run using the stored configuration.

    Args:
        x_agent_id (None | str | Unset):
        body (AgentBuilderRunRequest): Request schema for running an agent config

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentBuilderRunResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        x_agent_id=x_agent_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: AgentBuilderRunRequest,
    x_agent_id: None | str | Unset = UNSET,
) -> AgentBuilderRunResponse | HTTPValidationError | None:
    """Run agent

     Execute an agent run using the stored configuration.

    Args:
        x_agent_id (None | str | Unset):
        body (AgentBuilderRunRequest): Request schema for running an agent config

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentBuilderRunResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
        x_agent_id=x_agent_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AgentBuilderRunRequest,
    x_agent_id: None | str | Unset = UNSET,
) -> Response[AgentBuilderRunResponse | HTTPValidationError]:
    """Run agent

     Execute an agent run using the stored configuration.

    Args:
        x_agent_id (None | str | Unset):
        body (AgentBuilderRunRequest): Request schema for running an agent config

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentBuilderRunResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        x_agent_id=x_agent_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: AgentBuilderRunRequest,
    x_agent_id: None | str | Unset = UNSET,
) -> AgentBuilderRunResponse | HTTPValidationError | None:
    """Run agent

     Execute an agent run using the stored configuration.

    Args:
        x_agent_id (None | str | Unset):
        body (AgentBuilderRunRequest): Request schema for running an agent config

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentBuilderRunResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_agent_id=x_agent_id,
        )
    ).parsed
