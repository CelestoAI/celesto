from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.telegram_bot_response import TelegramBotResponse
from ...models.telegram_bot_update_request import TelegramBotUpdateRequest
from typing import cast


def _get_kwargs(
    bot_id: str,
    *,
    body: TelegramBotUpdateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/telegram-bots/{bot_id}".format(
            bot_id=quote(str(bot_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TelegramBotResponse | None:
    if response.status_code == 200:
        response_200 = TelegramBotResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TelegramBotResponse]:
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
    body: TelegramBotUpdateRequest,
) -> Response[HTTPValidationError | TelegramBotResponse]:
    """Update a Telegram bot

     Update a bot.

    Repointing `agent_id` moves the bot's existing chats onto the new agent too,
    so conversations already under way continue with the new agent instead of
    splitting. Set `status` to `disabled` to stop answering without losing any
    history.

    Args:
        bot_id (str):
        body (TelegramBotUpdateRequest): Patch a bot. Omitted fields are left unchanged.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TelegramBotResponse]
    """

    kwargs = _get_kwargs(
        bot_id=bot_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    bot_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TelegramBotUpdateRequest,
) -> HTTPValidationError | TelegramBotResponse | None:
    """Update a Telegram bot

     Update a bot.

    Repointing `agent_id` moves the bot's existing chats onto the new agent too,
    so conversations already under way continue with the new agent instead of
    splitting. Set `status` to `disabled` to stop answering without losing any
    history.

    Args:
        bot_id (str):
        body (TelegramBotUpdateRequest): Patch a bot. Omitted fields are left unchanged.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TelegramBotResponse
    """

    return sync_detailed(
        bot_id=bot_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    bot_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TelegramBotUpdateRequest,
) -> Response[HTTPValidationError | TelegramBotResponse]:
    """Update a Telegram bot

     Update a bot.

    Repointing `agent_id` moves the bot's existing chats onto the new agent too,
    so conversations already under way continue with the new agent instead of
    splitting. Set `status` to `disabled` to stop answering without losing any
    history.

    Args:
        bot_id (str):
        body (TelegramBotUpdateRequest): Patch a bot. Omitted fields are left unchanged.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TelegramBotResponse]
    """

    kwargs = _get_kwargs(
        bot_id=bot_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    bot_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TelegramBotUpdateRequest,
) -> HTTPValidationError | TelegramBotResponse | None:
    """Update a Telegram bot

     Update a bot.

    Repointing `agent_id` moves the bot's existing chats onto the new agent too,
    so conversations already under way continue with the new agent instead of
    splitting. Set `status` to `disabled` to stop answering without losing any
    history.

    Args:
        bot_id (str):
        body (TelegramBotUpdateRequest): Patch a bot. Omitted fields are left unchanged.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TelegramBotResponse
    """

    return (
        await asyncio_detailed(
            bot_id=bot_id,
            client=client,
            body=body,
        )
    ).parsed
