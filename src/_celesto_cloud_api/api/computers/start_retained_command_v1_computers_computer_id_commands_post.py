from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.command_start import CommandStart
from ...models.computer_validation_error_response import ComputerValidationErrorResponse
from ...models.start_retained_command_v1_computers_computer_id_commands_post_response_start_retained_command_v1_computers_computer_id_commands_post import (
    StartRetainedCommandV1ComputersComputerIdCommandsPostResponseStartRetainedCommandV1ComputersComputerIdCommandsPost,
)
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    computer_id: str,
    *,
    body: CommandStart,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/computers/{computer_id}/commands".format(
            computer_id=quote(str(computer_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ComputerValidationErrorResponse
    | StartRetainedCommandV1ComputersComputerIdCommandsPostResponseStartRetainedCommandV1ComputersComputerIdCommandsPost
    | None
):
    if response.status_code == 200:
        response_200 = StartRetainedCommandV1ComputersComputerIdCommandsPostResponseStartRetainedCommandV1ComputersComputerIdCommandsPost.from_dict(
            response.json()
        )

        return response_200

    if response.status_code == 422:
        response_422 = ComputerValidationErrorResponse.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ComputerValidationErrorResponse
    | StartRetainedCommandV1ComputersComputerIdCommandsPostResponseStartRetainedCommandV1ComputersComputerIdCommandsPost
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CommandStart,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    ComputerValidationErrorResponse
    | StartRetainedCommandV1ComputersComputerIdCommandsPostResponseStartRetainedCommandV1ComputersComputerIdCommandsPost
]:
    """Start Retained Command

    Args:
        computer_id (str):
        x_current_organization (str | Unset): Current organization ID
        body (CommandStart):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ComputerValidationErrorResponse | StartRetainedCommandV1ComputersComputerIdCommandsPostResponseStartRetainedCommandV1ComputersComputerIdCommandsPost]
    """

    kwargs = _get_kwargs(
        computer_id=computer_id,
        body=body,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CommandStart,
    x_current_organization: str | Unset = UNSET,
) -> (
    ComputerValidationErrorResponse
    | StartRetainedCommandV1ComputersComputerIdCommandsPostResponseStartRetainedCommandV1ComputersComputerIdCommandsPost
    | None
):
    """Start Retained Command

    Args:
        computer_id (str):
        x_current_organization (str | Unset): Current organization ID
        body (CommandStart):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ComputerValidationErrorResponse | StartRetainedCommandV1ComputersComputerIdCommandsPostResponseStartRetainedCommandV1ComputersComputerIdCommandsPost
    """

    return sync_detailed(
        computer_id=computer_id,
        client=client,
        body=body,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CommandStart,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    ComputerValidationErrorResponse
    | StartRetainedCommandV1ComputersComputerIdCommandsPostResponseStartRetainedCommandV1ComputersComputerIdCommandsPost
]:
    """Start Retained Command

    Args:
        computer_id (str):
        x_current_organization (str | Unset): Current organization ID
        body (CommandStart):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ComputerValidationErrorResponse | StartRetainedCommandV1ComputersComputerIdCommandsPostResponseStartRetainedCommandV1ComputersComputerIdCommandsPost]
    """

    kwargs = _get_kwargs(
        computer_id=computer_id,
        body=body,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CommandStart,
    x_current_organization: str | Unset = UNSET,
) -> (
    ComputerValidationErrorResponse
    | StartRetainedCommandV1ComputersComputerIdCommandsPostResponseStartRetainedCommandV1ComputersComputerIdCommandsPost
    | None
):
    """Start Retained Command

    Args:
        computer_id (str):
        x_current_organization (str | Unset): Current organization ID
        body (CommandStart):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ComputerValidationErrorResponse | StartRetainedCommandV1ComputersComputerIdCommandsPostResponseStartRetainedCommandV1ComputersComputerIdCommandsPost
    """

    return (
        await asyncio_detailed(
            computer_id=computer_id,
            client=client,
            body=body,
            x_current_organization=x_current_organization,
        )
    ).parsed
