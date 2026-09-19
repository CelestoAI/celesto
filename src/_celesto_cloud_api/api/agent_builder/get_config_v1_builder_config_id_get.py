from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.agent_builder_response import AgentBuilderResponse
from ...models.http_validation_error import HTTPValidationError
from typing import cast


def _get_kwargs(
    config_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/builder/{config_id}".format(
            config_id=quote(str(config_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AgentBuilderResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AgentBuilderResponse.from_dict(response.json())

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
) -> Response[AgentBuilderResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    config_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[AgentBuilderResponse | HTTPValidationError]:
    """Get agent config details

     Get agent config by ID.

    Args:
        config_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentBuilderResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        config_id=config_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    config_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> AgentBuilderResponse | HTTPValidationError | None:
    """Get agent config details

     Get agent config by ID.

    Args:
        config_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentBuilderResponse | HTTPValidationError
    """

    return sync_detailed(
        config_id=config_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    config_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[AgentBuilderResponse | HTTPValidationError]:
    """Get agent config details

     Get agent config by ID.

    Args:
        config_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentBuilderResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        config_id=config_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    config_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> AgentBuilderResponse | HTTPValidationError | None:
    """Get agent config details

     Get agent config by ID.

    Args:
        config_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentBuilderResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            config_id=config_id,
            client=client,
        )
    ).parsed
