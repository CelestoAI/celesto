from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.delete_account_v1_toolhub_provider_accounts_tool_provider_id_delete_response_delete_account_v1_toolhub_provider_accounts_tool_provider_id_delete import (
    DeleteAccountV1ToolhubProviderAccountsToolProviderIdDeleteResponseDeleteAccountV1ToolhubProviderAccountsToolProviderIdDelete,
)
from ...models.http_validation_error import HTTPValidationError
from typing import cast


def _get_kwargs(
    tool_provider_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/v1/toolhub_provider/accounts/{tool_provider_id}".format(
            tool_provider_id=quote(str(tool_provider_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    DeleteAccountV1ToolhubProviderAccountsToolProviderIdDeleteResponseDeleteAccountV1ToolhubProviderAccountsToolProviderIdDelete
    | HTTPValidationError
    | None
):
    if response.status_code == 200:
        response_200 = DeleteAccountV1ToolhubProviderAccountsToolProviderIdDeleteResponseDeleteAccountV1ToolhubProviderAccountsToolProviderIdDelete.from_dict(
            response.json()
        )

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
) -> Response[
    DeleteAccountV1ToolhubProviderAccountsToolProviderIdDeleteResponseDeleteAccountV1ToolhubProviderAccountsToolProviderIdDelete
    | HTTPValidationError
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    tool_provider_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    DeleteAccountV1ToolhubProviderAccountsToolProviderIdDeleteResponseDeleteAccountV1ToolhubProviderAccountsToolProviderIdDelete
    | HTTPValidationError
]:
    """Delete Account

     Delete a connected tool for a user

    Args:
        tool_provider_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteAccountV1ToolhubProviderAccountsToolProviderIdDeleteResponseDeleteAccountV1ToolhubProviderAccountsToolProviderIdDelete | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        tool_provider_id=tool_provider_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tool_provider_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    DeleteAccountV1ToolhubProviderAccountsToolProviderIdDeleteResponseDeleteAccountV1ToolhubProviderAccountsToolProviderIdDelete
    | HTTPValidationError
    | None
):
    """Delete Account

     Delete a connected tool for a user

    Args:
        tool_provider_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteAccountV1ToolhubProviderAccountsToolProviderIdDeleteResponseDeleteAccountV1ToolhubProviderAccountsToolProviderIdDelete | HTTPValidationError
    """

    return sync_detailed(
        tool_provider_id=tool_provider_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    tool_provider_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    DeleteAccountV1ToolhubProviderAccountsToolProviderIdDeleteResponseDeleteAccountV1ToolhubProviderAccountsToolProviderIdDelete
    | HTTPValidationError
]:
    """Delete Account

     Delete a connected tool for a user

    Args:
        tool_provider_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteAccountV1ToolhubProviderAccountsToolProviderIdDeleteResponseDeleteAccountV1ToolhubProviderAccountsToolProviderIdDelete | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        tool_provider_id=tool_provider_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tool_provider_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    DeleteAccountV1ToolhubProviderAccountsToolProviderIdDeleteResponseDeleteAccountV1ToolhubProviderAccountsToolProviderIdDelete
    | HTTPValidationError
    | None
):
    """Delete Account

     Delete a connected tool for a user

    Args:
        tool_provider_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteAccountV1ToolhubProviderAccountsToolProviderIdDeleteResponseDeleteAccountV1ToolhubProviderAccountsToolProviderIdDelete | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            tool_provider_id=tool_provider_id,
            client=client,
        )
    ).parsed
