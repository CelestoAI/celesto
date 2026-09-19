from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.telegram_bot_create_request import TelegramBotCreateRequest
from ...models.telegram_bot_response import TelegramBotResponse
from typing import cast


def _get_kwargs(
    *,
    body: TelegramBotCreateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/telegram-bots",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TelegramBotResponse | None:
    if response.status_code == 201:
        response_201 = TelegramBotResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TelegramBotResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TelegramBotCreateRequest,
) -> Response[HTTPValidationError | TelegramBotResponse]:
    """Register a Telegram bot

     Register a bot created with @BotFather and point Telegram at this API.

    The token is validated against Telegram before anything is stored, then
    encrypted at rest. Each chat the bot receives gets its own conversation
    thread, keyed on a `subject` of `telegram:{chat_id}`.

    Args:
        body (TelegramBotCreateRequest): Register a bot created with Telegram's @BotFather.

            Supply `project_id`, or `organization_id` to use that organization's
            default project.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TelegramBotResponse]
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
    body: TelegramBotCreateRequest,
) -> HTTPValidationError | TelegramBotResponse | None:
    """Register a Telegram bot

     Register a bot created with @BotFather and point Telegram at this API.

    The token is validated against Telegram before anything is stored, then
    encrypted at rest. Each chat the bot receives gets its own conversation
    thread, keyed on a `subject` of `telegram:{chat_id}`.

    Args:
        body (TelegramBotCreateRequest): Register a bot created with Telegram's @BotFather.

            Supply `project_id`, or `organization_id` to use that organization's
            default project.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TelegramBotResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TelegramBotCreateRequest,
) -> Response[HTTPValidationError | TelegramBotResponse]:
    """Register a Telegram bot

     Register a bot created with @BotFather and point Telegram at this API.

    The token is validated against Telegram before anything is stored, then
    encrypted at rest. Each chat the bot receives gets its own conversation
    thread, keyed on a `subject` of `telegram:{chat_id}`.

    Args:
        body (TelegramBotCreateRequest): Register a bot created with Telegram's @BotFather.

            Supply `project_id`, or `organization_id` to use that organization's
            default project.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TelegramBotResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: TelegramBotCreateRequest,
) -> HTTPValidationError | TelegramBotResponse | None:
    """Register a Telegram bot

     Register a bot created with @BotFather and point Telegram at this API.

    The token is validated against Telegram before anything is stored, then
    encrypted at rest. Each chat the bot receives gets its own conversation
    thread, keyed on a `subject` of `telegram:{chat_id}`.

    Args:
        body (TelegramBotCreateRequest): Register a bot created with Telegram's @BotFather.

            Supply `project_id`, or `organization_id` to use that organization's
            default project.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TelegramBotResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
