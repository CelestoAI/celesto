from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.thread_clear_response import ThreadClearResponse
from typing import cast


def _get_kwargs(
    thread_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/v1/threads/{thread_id}/messages".format(
            thread_id=quote(str(thread_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ThreadClearResponse | None:
    if response.status_code == 200:
        response_200 = ThreadClearResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | ThreadClearResponse]:
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
) -> Response[HTTPValidationError | ThreadClearResponse]:
    """Clear a thread's messages

     Delete every message while keeping the thread, its subject, and metadata.

    Takes the same lock a run does. Clearing is a second writer to the thread:
    without it, a run could reserve a sequence number, the clear could reset the
    allocator, and the run's insert would land on a number the allocator hands
    out again later.

    Args:
        thread_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ThreadClearResponse]
    """

    kwargs = _get_kwargs(
        thread_id=thread_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    thread_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | ThreadClearResponse | None:
    """Clear a thread's messages

     Delete every message while keeping the thread, its subject, and metadata.

    Takes the same lock a run does. Clearing is a second writer to the thread:
    without it, a run could reserve a sequence number, the clear could reset the
    allocator, and the run's insert would land on a number the allocator hands
    out again later.

    Args:
        thread_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ThreadClearResponse
    """

    return sync_detailed(
        thread_id=thread_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    thread_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | ThreadClearResponse]:
    """Clear a thread's messages

     Delete every message while keeping the thread, its subject, and metadata.

    Takes the same lock a run does. Clearing is a second writer to the thread:
    without it, a run could reserve a sequence number, the clear could reset the
    allocator, and the run's insert would land on a number the allocator hands
    out again later.

    Args:
        thread_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ThreadClearResponse]
    """

    kwargs = _get_kwargs(
        thread_id=thread_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    thread_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | ThreadClearResponse | None:
    """Clear a thread's messages

     Delete every message while keeping the thread, its subject, and metadata.

    Takes the same lock a run does. Clearing is a second writer to the thread:
    without it, a run could reserve a sequence number, the clear could reset the
    allocator, and the run's insert would land on a number the allocator hands
    out again later.

    Args:
        thread_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ThreadClearResponse
    """

    return (
        await asyncio_detailed(
            thread_id=thread_id,
            client=client,
        )
    ).parsed
