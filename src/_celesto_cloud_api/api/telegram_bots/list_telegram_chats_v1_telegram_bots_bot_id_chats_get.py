from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.telegram_chat_list_response import TelegramChatListResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    bot_id: str,
    *,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params["offset"] = offset

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/telegram-bots/{bot_id}/chats".format(
            bot_id=quote(str(bot_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TelegramChatListResponse | None:
    if response.status_code == 200:
        response_200 = TelegramChatListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TelegramChatListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    bot_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> Response[HTTPValidationError | TelegramChatListResponse]:
    """List a bot's chats

     List the chats this bot is in and the thread backing each one.

    Read a chat's history through `GET /threads/{thread_id}/messages`.

    Args:
        bot_id (str):
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TelegramChatListResponse]
    """

    kwargs = _get_kwargs(
        bot_id=bot_id,
        limit=limit,
        offset=offset,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    bot_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> HTTPValidationError | TelegramChatListResponse | None:
    """List a bot's chats

     List the chats this bot is in and the thread backing each one.

    Read a chat's history through `GET /threads/{thread_id}/messages`.

    Args:
        bot_id (str):
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TelegramChatListResponse
    """

    return sync_detailed(
        bot_id=bot_id,
        client=client,
        limit=limit,
        offset=offset,
    ).parsed


async def asyncio_detailed(
    bot_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> Response[HTTPValidationError | TelegramChatListResponse]:
    """List a bot's chats

     List the chats this bot is in and the thread backing each one.

    Read a chat's history through `GET /threads/{thread_id}/messages`.

    Args:
        bot_id (str):
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TelegramChatListResponse]
    """

    kwargs = _get_kwargs(
        bot_id=bot_id,
        limit=limit,
        offset=offset,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    bot_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> HTTPValidationError | TelegramChatListResponse | None:
    """List a bot's chats

     List the chats this bot is in and the thread backing each one.

    Read a chat's history through `GET /threads/{thread_id}/messages`.

    Args:
        bot_id (str):
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TelegramChatListResponse
    """

    return (
        await asyncio_detailed(
            bot_id=bot_id,
            client=client,
            limit=limit,
            offset=offset,
        )
    ).parsed
