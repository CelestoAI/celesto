from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.session_messages_response import SessionMessagesResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    session_id: str,
    *,
    limit: int | Unset = 50,
    before_seq: int | None | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

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
        "url": "/v1/sessions/{session_id}".format(
            session_id=quote(str(session_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | SessionMessagesResponse | None:
    if response.status_code == 200:
        response_200 = SessionMessagesResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | SessionMessagesResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    session_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    before_seq: int | None | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | SessionMessagesResponse]:
    """Get a session and its transcript

    Args:
        session_id (str):
        limit (int | Unset):  Default: 50.
        before_seq (int | None | Unset):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SessionMessagesResponse]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        limit=limit,
        before_seq=before_seq,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    session_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    before_seq: int | None | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | SessionMessagesResponse | None:
    """Get a session and its transcript

    Args:
        session_id (str):
        limit (int | Unset):  Default: 50.
        before_seq (int | None | Unset):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SessionMessagesResponse
    """

    return sync_detailed(
        session_id=session_id,
        client=client,
        limit=limit,
        before_seq=before_seq,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    session_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    before_seq: int | None | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | SessionMessagesResponse]:
    """Get a session and its transcript

    Args:
        session_id (str):
        limit (int | Unset):  Default: 50.
        before_seq (int | None | Unset):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SessionMessagesResponse]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        limit=limit,
        before_seq=before_seq,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    session_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    before_seq: int | None | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | SessionMessagesResponse | None:
    """Get a session and its transcript

    Args:
        session_id (str):
        limit (int | Unset):  Default: 50.
        before_seq (int | None | Unset):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SessionMessagesResponse
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            client=client,
            limit=limit,
            before_seq=before_seq,
            x_current_organization=x_current_organization,
        )
    ).parsed
