from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.telegram_bot_response import TelegramBotResponse
from typing import cast


def _get_kwargs(
    bot_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/telegram-bots/{bot_id}".format(
            bot_id=quote(str(bot_id), safe=""),
        ),
    }

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
) -> Response[HTTPValidationError | TelegramBotResponse]:
    """Get a Telegram bot

    Args:
        bot_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TelegramBotResponse]
    """

    kwargs = _get_kwargs(
        bot_id=bot_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    bot_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | TelegramBotResponse | None:
    """Get a Telegram bot

    Args:
        bot_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TelegramBotResponse
    """

    return sync_detailed(
        bot_id=bot_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    bot_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | TelegramBotResponse]:
    """Get a Telegram bot

    Args:
        bot_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TelegramBotResponse]
    """

    kwargs = _get_kwargs(
        bot_id=bot_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    bot_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | TelegramBotResponse | None:
    """Get a Telegram bot

    Args:
        bot_id (str):

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
        )
    ).parsed
