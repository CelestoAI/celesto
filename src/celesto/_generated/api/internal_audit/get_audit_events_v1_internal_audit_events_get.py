from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.get_audit_events_v1_internal_audit_events_get_response_200_item import (
    GetAuditEventsV1InternalAuditEventsGetResponse200Item,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast
import datetime


def _get_kwargs(
    *,
    event_type: None | str | Unset = UNSET,
    org_id: None | str | Unset = UNSET,
    actor_id: None | str | Unset = UNSET,
    outcome: None | str | Unset = UNSET,
    from_ts: datetime.datetime | None | Unset = UNSET,
    to_ts: datetime.datetime | None | Unset = UNSET,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    params: dict[str, Any] = {}

    json_event_type: None | str | Unset
    if isinstance(event_type, Unset):
        json_event_type = UNSET
    else:
        json_event_type = event_type
    params["event_type"] = json_event_type

    json_org_id: None | str | Unset
    if isinstance(org_id, Unset):
        json_org_id = UNSET
    else:
        json_org_id = org_id
    params["org_id"] = json_org_id

    json_actor_id: None | str | Unset
    if isinstance(actor_id, Unset):
        json_actor_id = UNSET
    else:
        json_actor_id = actor_id
    params["actor_id"] = json_actor_id

    json_outcome: None | str | Unset
    if isinstance(outcome, Unset):
        json_outcome = UNSET
    else:
        json_outcome = outcome
    params["outcome"] = json_outcome

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
        "url": "/v1/internal/audit/events",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | list[GetAuditEventsV1InternalAuditEventsGetResponse200Item]
    | None
):
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = (
                GetAuditEventsV1InternalAuditEventsGetResponse200Item.from_dict(
                    response_200_item_data
                )
            )

            response_200.append(response_200_item)

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
    HTTPValidationError | list[GetAuditEventsV1InternalAuditEventsGetResponse200Item]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    event_type: None | str | Unset = UNSET,
    org_id: None | str | Unset = UNSET,
    actor_id: None | str | Unset = UNSET,
    outcome: None | str | Unset = UNSET,
    from_ts: datetime.datetime | None | Unset = UNSET,
    to_ts: datetime.datetime | None | Unset = UNSET,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    HTTPValidationError | list[GetAuditEventsV1InternalAuditEventsGetResponse200Item]
]:
    """Get Audit Events

     Query audit events (Super Org members only).

    Supports filtering by event type, org, actor, outcome, and time range.
    Results are ordered by timestamp descending (newest first).
    Sensitive fields (ip_address, user_agent, extra_data) redacted for non-owners.

    Args:
        event_type (None | str | Unset): Filter by event type prefix
        org_id (None | str | Unset): Filter by organization ID
        actor_id (None | str | Unset): Filter by actor ID
        outcome (None | str | Unset): Filter by outcome
        from_ts (datetime.datetime | None | Unset): From timestamp (inclusive)
        to_ts (datetime.datetime | None | Unset): To timestamp (inclusive)
        limit (int | Unset): Max results Default: 100.
        offset (int | Unset): Offset for pagination Default: 0.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[GetAuditEventsV1InternalAuditEventsGetResponse200Item]]
    """

    kwargs = _get_kwargs(
        event_type=event_type,
        org_id=org_id,
        actor_id=actor_id,
        outcome=outcome,
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
    event_type: None | str | Unset = UNSET,
    org_id: None | str | Unset = UNSET,
    actor_id: None | str | Unset = UNSET,
    outcome: None | str | Unset = UNSET,
    from_ts: datetime.datetime | None | Unset = UNSET,
    to_ts: datetime.datetime | None | Unset = UNSET,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> (
    HTTPValidationError
    | list[GetAuditEventsV1InternalAuditEventsGetResponse200Item]
    | None
):
    """Get Audit Events

     Query audit events (Super Org members only).

    Supports filtering by event type, org, actor, outcome, and time range.
    Results are ordered by timestamp descending (newest first).
    Sensitive fields (ip_address, user_agent, extra_data) redacted for non-owners.

    Args:
        event_type (None | str | Unset): Filter by event type prefix
        org_id (None | str | Unset): Filter by organization ID
        actor_id (None | str | Unset): Filter by actor ID
        outcome (None | str | Unset): Filter by outcome
        from_ts (datetime.datetime | None | Unset): From timestamp (inclusive)
        to_ts (datetime.datetime | None | Unset): To timestamp (inclusive)
        limit (int | Unset): Max results Default: 100.
        offset (int | Unset): Offset for pagination Default: 0.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[GetAuditEventsV1InternalAuditEventsGetResponse200Item]
    """

    return sync_detailed(
        client=client,
        event_type=event_type,
        org_id=org_id,
        actor_id=actor_id,
        outcome=outcome,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
        offset=offset,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    event_type: None | str | Unset = UNSET,
    org_id: None | str | Unset = UNSET,
    actor_id: None | str | Unset = UNSET,
    outcome: None | str | Unset = UNSET,
    from_ts: datetime.datetime | None | Unset = UNSET,
    to_ts: datetime.datetime | None | Unset = UNSET,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    HTTPValidationError | list[GetAuditEventsV1InternalAuditEventsGetResponse200Item]
]:
    """Get Audit Events

     Query audit events (Super Org members only).

    Supports filtering by event type, org, actor, outcome, and time range.
    Results are ordered by timestamp descending (newest first).
    Sensitive fields (ip_address, user_agent, extra_data) redacted for non-owners.

    Args:
        event_type (None | str | Unset): Filter by event type prefix
        org_id (None | str | Unset): Filter by organization ID
        actor_id (None | str | Unset): Filter by actor ID
        outcome (None | str | Unset): Filter by outcome
        from_ts (datetime.datetime | None | Unset): From timestamp (inclusive)
        to_ts (datetime.datetime | None | Unset): To timestamp (inclusive)
        limit (int | Unset): Max results Default: 100.
        offset (int | Unset): Offset for pagination Default: 0.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[GetAuditEventsV1InternalAuditEventsGetResponse200Item]]
    """

    kwargs = _get_kwargs(
        event_type=event_type,
        org_id=org_id,
        actor_id=actor_id,
        outcome=outcome,
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
    event_type: None | str | Unset = UNSET,
    org_id: None | str | Unset = UNSET,
    actor_id: None | str | Unset = UNSET,
    outcome: None | str | Unset = UNSET,
    from_ts: datetime.datetime | None | Unset = UNSET,
    to_ts: datetime.datetime | None | Unset = UNSET,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> (
    HTTPValidationError
    | list[GetAuditEventsV1InternalAuditEventsGetResponse200Item]
    | None
):
    """Get Audit Events

     Query audit events (Super Org members only).

    Supports filtering by event type, org, actor, outcome, and time range.
    Results are ordered by timestamp descending (newest first).
    Sensitive fields (ip_address, user_agent, extra_data) redacted for non-owners.

    Args:
        event_type (None | str | Unset): Filter by event type prefix
        org_id (None | str | Unset): Filter by organization ID
        actor_id (None | str | Unset): Filter by actor ID
        outcome (None | str | Unset): Filter by outcome
        from_ts (datetime.datetime | None | Unset): From timestamp (inclusive)
        to_ts (datetime.datetime | None | Unset): To timestamp (inclusive)
        limit (int | Unset): Max results Default: 100.
        offset (int | Unset): Offset for pagination Default: 0.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[GetAuditEventsV1InternalAuditEventsGetResponse200Item]
    """

    return (
        await asyncio_detailed(
            client=client,
            event_type=event_type,
            org_id=org_id,
            actor_id=actor_id,
            outcome=outcome,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=limit,
            offset=offset,
            x_current_organization=x_current_organization,
        )
    ).parsed
