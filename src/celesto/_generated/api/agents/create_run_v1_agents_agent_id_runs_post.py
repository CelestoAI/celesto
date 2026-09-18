from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.run_create_request import RunCreateRequest
from ...models.run_response import RunResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    agent_id: str,
    *,
    body: RunCreateRequest,
    idempotency_key: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/agents/{agent_id}/runs".format(
            agent_id=quote(str(agent_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | RunResponse | None:
    if response.status_code == 200:
        response_200 = RunResponse.from_dict(response.json())

        return response_200

    if response.status_code == 402:
        response_402 = cast(Any, None)
        return response_402

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if response.status_code == 409:
        response_409 = cast(Any, None)
        return response_409

    if response.status_code == 422:
        response_422 = cast(Any, None)
        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | RunResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: RunCreateRequest,
    idempotency_key: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[Any | RunResponse]:
    """Run an agent

     Execute a run. SSE when ``stream: true``, JSON envelope otherwise.

    Errors: 402 budget_exceeded · 404 agent/session · 409 session_busy /
    idempotency_conflict / provider_not_connected / agent_archived /
    session_agent_mismatch · 422 session_end_user_mismatch /
    model_requires_own_key.

    Args:
        agent_id (str):
        idempotency_key (None | str | Unset):
        x_current_organization (str | Unset): Current organization ID
        body (RunCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | RunResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        body=body,
        idempotency_key=idempotency_key,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: RunCreateRequest,
    idempotency_key: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Any | RunResponse | None:
    """Run an agent

     Execute a run. SSE when ``stream: true``, JSON envelope otherwise.

    Errors: 402 budget_exceeded · 404 agent/session · 409 session_busy /
    idempotency_conflict / provider_not_connected / agent_archived /
    session_agent_mismatch · 422 session_end_user_mismatch /
    model_requires_own_key.

    Args:
        agent_id (str):
        idempotency_key (None | str | Unset):
        x_current_organization (str | Unset): Current organization ID
        body (RunCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | RunResponse
    """

    return sync_detailed(
        agent_id=agent_id,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: RunCreateRequest,
    idempotency_key: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[Any | RunResponse]:
    """Run an agent

     Execute a run. SSE when ``stream: true``, JSON envelope otherwise.

    Errors: 402 budget_exceeded · 404 agent/session · 409 session_busy /
    idempotency_conflict / provider_not_connected / agent_archived /
    session_agent_mismatch · 422 session_end_user_mismatch /
    model_requires_own_key.

    Args:
        agent_id (str):
        idempotency_key (None | str | Unset):
        x_current_organization (str | Unset): Current organization ID
        body (RunCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | RunResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        body=body,
        idempotency_key=idempotency_key,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: RunCreateRequest,
    idempotency_key: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Any | RunResponse | None:
    """Run an agent

     Execute a run. SSE when ``stream: true``, JSON envelope otherwise.

    Errors: 402 budget_exceeded · 404 agent/session · 409 session_busy /
    idempotency_conflict / provider_not_connected / agent_archived /
    session_agent_mismatch · 422 session_end_user_mismatch /
    model_requires_own_key.

    Args:
        agent_id (str):
        idempotency_key (None | str | Unset):
        x_current_organization (str | Unset): Current organization ID
        body (RunCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | RunResponse
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
            x_current_organization=x_current_organization,
        )
    ).parsed
