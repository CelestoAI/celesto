from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.get_all_connected_tools_for_user_v1_toolhub_provider_connected_tools_get_response_200_item import (
    GetAllConnectedToolsForUserV1ToolhubProviderConnectedToolsGetResponse200Item,
)
from typing import cast


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/toolhub_provider/connected-tools",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    list[GetAllConnectedToolsForUserV1ToolhubProviderConnectedToolsGetResponse200Item]
    | None
):
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = GetAllConnectedToolsForUserV1ToolhubProviderConnectedToolsGetResponse200Item.from_dict(
                response_200_item_data
            )

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    list[GetAllConnectedToolsForUserV1ToolhubProviderConnectedToolsGetResponse200Item]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    list[GetAllConnectedToolsForUserV1ToolhubProviderConnectedToolsGetResponse200Item]
]:
    """Get All Connected Tools For User

     Get all connected tools for a user

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[GetAllConnectedToolsForUserV1ToolhubProviderConnectedToolsGetResponse200Item]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> (
    list[GetAllConnectedToolsForUserV1ToolhubProviderConnectedToolsGetResponse200Item]
    | None
):
    """Get All Connected Tools For User

     Get all connected tools for a user

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[GetAllConnectedToolsForUserV1ToolhubProviderConnectedToolsGetResponse200Item]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    list[GetAllConnectedToolsForUserV1ToolhubProviderConnectedToolsGetResponse200Item]
]:
    """Get All Connected Tools For User

     Get all connected tools for a user

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[GetAllConnectedToolsForUserV1ToolhubProviderConnectedToolsGetResponse200Item]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> (
    list[GetAllConnectedToolsForUserV1ToolhubProviderConnectedToolsGetResponse200Item]
    | None
):
    """Get All Connected Tools For User

     Get all connected tools for a user

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[GetAllConnectedToolsForUserV1ToolhubProviderConnectedToolsGetResponse200Item]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
