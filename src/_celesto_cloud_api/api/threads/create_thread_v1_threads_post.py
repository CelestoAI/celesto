from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.thread_create_request import ThreadCreateRequest
from ...models.thread_response import ThreadResponse
from typing import cast


def _get_kwargs(
    *,
    body: ThreadCreateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/threads",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ThreadResponse | None:
    if response.status_code == 201:
        response_201 = ThreadResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | ThreadResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ThreadCreateRequest,
) -> Response[HTTPValidationError | ThreadResponse]:
    """Create a conversation thread

     Create a thread.

    Pass `subject` to bind the thread to one of your own end users; it shares a
    namespace with delegated tool access, so conversation and credentials
    resolve from the same identifier.

    Args:
        body (ThreadCreateRequest): Create a conversation thread.

            Supply `project_id`, or `organization_id` to use that organization's
            default project.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ThreadResponse]
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
    body: ThreadCreateRequest,
) -> HTTPValidationError | ThreadResponse | None:
    """Create a conversation thread

     Create a thread.

    Pass `subject` to bind the thread to one of your own end users; it shares a
    namespace with delegated tool access, so conversation and credentials
    resolve from the same identifier.

    Args:
        body (ThreadCreateRequest): Create a conversation thread.

            Supply `project_id`, or `organization_id` to use that organization's
            default project.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ThreadResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ThreadCreateRequest,
) -> Response[HTTPValidationError | ThreadResponse]:
    """Create a conversation thread

     Create a thread.

    Pass `subject` to bind the thread to one of your own end users; it shares a
    namespace with delegated tool access, so conversation and credentials
    resolve from the same identifier.

    Args:
        body (ThreadCreateRequest): Create a conversation thread.

            Supply `project_id`, or `organization_id` to use that organization's
            default project.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ThreadResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: ThreadCreateRequest,
) -> HTTPValidationError | ThreadResponse | None:
    """Create a conversation thread

     Create a thread.

    Pass `subject` to bind the thread to one of your own end users; it shares a
    namespace with delegated tool access, so conversation and credentials
    resolve from the same identifier.

    Args:
        body (ThreadCreateRequest): Create a conversation thread.

            Supply `project_id`, or `organization_id` to use that organization's
            default project.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ThreadResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
