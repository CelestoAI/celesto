from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.trace_list_response import TraceListResponse
from ...types import UNSET, Unset
from typing import cast
import datetime


def _get_kwargs(
    *,
    has_error: bool | None | Unset = UNSET,
    group_id: None | str | Unset = UNSET,
    from_ts: datetime.datetime | None | Unset = UNSET,
    to_ts: datetime.datetime | None | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    params: dict[str, Any] = {}

    json_has_error: bool | None | Unset
    if isinstance(has_error, Unset):
        json_has_error = UNSET
    else:
        json_has_error = has_error
    params["has_error"] = json_has_error

    json_group_id: None | str | Unset
    if isinstance(group_id, Unset):
        json_group_id = UNSET
    else:
        json_group_id = group_id
    params["group_id"] = json_group_id

    json_from_ts: None | str | Unset
    if isinstance(from_ts, Unset):
        json_from_ts = UNSET
    elif isinstance(from_ts, datetime.datetime):
        json_from_ts = from_ts.isoformat()
    else:
        json_from_ts = from_ts
    params["from_ts"] = json_from_ts

    json_to_ts: None | str | Unset
    if isinstance(to_ts, Unset):
        json_to_ts = UNSET
    elif isinstance(to_ts, datetime.datetime):
        json_to_ts = to_ts.isoformat()
    else:
        json_to_ts = to_ts
    params["to_ts"] = json_to_ts

    params["limit"] = limit

    params["offset"] = offset

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/traces",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TraceListResponse | None:
    if response.status_code == 200:
        response_200 = TraceListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TraceListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    has_error: bool | None | Unset = UNSET,
    group_id: None | str | Unset = UNSET,
    from_ts: datetime.datetime | None | Unset = UNSET,
    to_ts: datetime.datetime | None | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | TraceListResponse]:
    """List traces

     List traces for the current organization with filtering.

    Returns a paginated list of traces with summary information.

    Args:
        has_error (bool | None | Unset): Filter by error status
        group_id (None | str | Unset): Filter by conversation/session group ID
        from_ts (datetime.datetime | None | Unset): Filter traces created after (UTC)
        to_ts (datetime.datetime | None | Unset): Filter traces created before (UTC)
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TraceListResponse]
    """

    kwargs = _get_kwargs(
        has_error=has_error,
        group_id=group_id,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
        offset=offset,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    has_error: bool | None | Unset = UNSET,
    group_id: None | str | Unset = UNSET,
    from_ts: datetime.datetime | None | Unset = UNSET,
    to_ts: datetime.datetime | None | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | TraceListResponse | None:
    """List traces

     List traces for the current organization with filtering.

    Returns a paginated list of traces with summary information.

    Args:
        has_error (bool | None | Unset): Filter by error status
        group_id (None | str | Unset): Filter by conversation/session group ID
        from_ts (datetime.datetime | None | Unset): Filter traces created after (UTC)
        to_ts (datetime.datetime | None | Unset): Filter traces created before (UTC)
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TraceListResponse
    """

    return sync_detailed(
        client=client,
        has_error=has_error,
        group_id=group_id,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
        offset=offset,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    has_error: bool | None | Unset = UNSET,
    group_id: None | str | Unset = UNSET,
    from_ts: datetime.datetime | None | Unset = UNSET,
    to_ts: datetime.datetime | None | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | TraceListResponse]:
    """List traces

     List traces for the current organization with filtering.

    Returns a paginated list of traces with summary information.

    Args:
        has_error (bool | None | Unset): Filter by error status
        group_id (None | str | Unset): Filter by conversation/session group ID
        from_ts (datetime.datetime | None | Unset): Filter traces created after (UTC)
        to_ts (datetime.datetime | None | Unset): Filter traces created before (UTC)
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TraceListResponse]
    """

    kwargs = _get_kwargs(
        has_error=has_error,
        group_id=group_id,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
        offset=offset,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    has_error: bool | None | Unset = UNSET,
    group_id: None | str | Unset = UNSET,
    from_ts: datetime.datetime | None | Unset = UNSET,
    to_ts: datetime.datetime | None | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | TraceListResponse | None:
    """List traces

     List traces for the current organization with filtering.

    Returns a paginated list of traces with summary information.

    Args:
        has_error (bool | None | Unset): Filter by error status
        group_id (None | str | Unset): Filter by conversation/session group ID
        from_ts (datetime.datetime | None | Unset): Filter traces created after (UTC)
        to_ts (datetime.datetime | None | Unset): Filter traces created before (UTC)
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TraceListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            has_error=has_error,
            group_id=group_id,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=limit,
            offset=offset,
            x_current_organization=x_current_organization,
        )
    ).parsed
