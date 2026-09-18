from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.thread_message_list_response import ThreadMessageListResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    thread_id: str,
    *,
    limit: int | Unset = 50,
    before_seq: int | None | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    json_before_seq: int | None | Unset
    if isinstance(before_seq, Unset):
        json_before_seq = UNSET
    else:
        json_before_seq = before_seq
    params["before_seq"] = json_before_seq

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/threads/{thread_id}/messages".format(
            thread_id=quote(str(thread_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ThreadMessageListResponse | None:
    if response.status_code == 200:
        response_200 = ThreadMessageListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | ThreadMessageListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    thread_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    before_seq: int | None | Unset = UNSET,
) -> Response[HTTPValidationError | ThreadMessageListResponse]:
    """List messages in a thread

     Page backwards through history, newest first.

    Args:
        thread_id (str):
        limit (int | Unset):  Default: 50.
        before_seq (int | None | Unset): Return messages older than this seq

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ThreadMessageListResponse]
    """

    kwargs = _get_kwargs(
        thread_id=thread_id,
        limit=limit,
        before_seq=before_seq,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    thread_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    before_seq: int | None | Unset = UNSET,
) -> HTTPValidationError | ThreadMessageListResponse | None:
    """List messages in a thread

     Page backwards through history, newest first.

    Args:
        thread_id (str):
        limit (int | Unset):  Default: 50.
        before_seq (int | None | Unset): Return messages older than this seq

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ThreadMessageListResponse
    """

    return sync_detailed(
        thread_id=thread_id,
        client=client,
        limit=limit,
        before_seq=before_seq,
    ).parsed


async def asyncio_detailed(
    thread_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    before_seq: int | None | Unset = UNSET,
) -> Response[HTTPValidationError | ThreadMessageListResponse]:
    """List messages in a thread

     Page backwards through history, newest first.

    Args:
        thread_id (str):
        limit (int | Unset):  Default: 50.
        before_seq (int | None | Unset): Return messages older than this seq

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ThreadMessageListResponse]
    """

    kwargs = _get_kwargs(
        thread_id=thread_id,
        limit=limit,
        before_seq=before_seq,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    thread_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    before_seq: int | None | Unset = UNSET,
) -> HTTPValidationError | ThreadMessageListResponse | None:
    """List messages in a thread

     Page backwards through history, newest first.

    Args:
        thread_id (str):
        limit (int | Unset):  Default: 50.
        before_seq (int | None | Unset): Return messages older than this seq

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ThreadMessageListResponse
    """

    return (
        await asyncio_detailed(
            thread_id=thread_id,
            client=client,
            limit=limit,
            before_seq=before_seq,
        )
    ).parsed
