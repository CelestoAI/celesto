from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.run_list_response import RunListResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    agent_id: None | str | Unset = UNSET,
    end_user_id: None | str | Unset = UNSET,
    session_id: None | str | Unset = UNSET,
    status: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    params: dict[str, Any] = {}

    json_agent_id: None | str | Unset
    if isinstance(agent_id, Unset):
        json_agent_id = UNSET
    else:
        json_agent_id = agent_id
    params["agent_id"] = json_agent_id

    json_end_user_id: None | str | Unset
    if isinstance(end_user_id, Unset):
        json_end_user_id = UNSET
    else:
        json_end_user_id = end_user_id
    params["end_user_id"] = json_end_user_id

    json_session_id: None | str | Unset
    if isinstance(session_id, Unset):
        json_session_id = UNSET
    else:
        json_session_id = session_id
    params["session_id"] = json_session_id

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    else:
        json_status = status
    params["status"] = json_status

    params["limit"] = limit

    params["offset"] = offset

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/runs",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | RunListResponse | None:
    if response.status_code == 200:
        response_200 = RunListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | RunListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    agent_id: None | str | Unset = UNSET,
    end_user_id: None | str | Unset = UNSET,
    session_id: None | str | Unset = UNSET,
    status: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | RunListResponse]:
    """List runs

     The org's run ledger, newest first.

    ``end_user_id`` takes the tenant's external identifier and resolves the
    surrogate internally — consistent with every response echoing only the
    external id. An unknown end user yields an empty page, not a 404: "no
    runs for this user" is an answer, not an error.

    Args:
        agent_id (None | str | Unset):
        end_user_id (None | str | Unset): The tenant's own end-user identifier
        session_id (None | str | Unset):
        status (None | str | Unset):
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RunListResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        end_user_id=end_user_id,
        session_id=session_id,
        status=status,
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
    agent_id: None | str | Unset = UNSET,
    end_user_id: None | str | Unset = UNSET,
    session_id: None | str | Unset = UNSET,
    status: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | RunListResponse | None:
    """List runs

     The org's run ledger, newest first.

    ``end_user_id`` takes the tenant's external identifier and resolves the
    surrogate internally — consistent with every response echoing only the
    external id. An unknown end user yields an empty page, not a 404: "no
    runs for this user" is an answer, not an error.

    Args:
        agent_id (None | str | Unset):
        end_user_id (None | str | Unset): The tenant's own end-user identifier
        session_id (None | str | Unset):
        status (None | str | Unset):
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RunListResponse
    """

    return sync_detailed(
        client=client,
        agent_id=agent_id,
        end_user_id=end_user_id,
        session_id=session_id,
        status=status,
        limit=limit,
        offset=offset,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    agent_id: None | str | Unset = UNSET,
    end_user_id: None | str | Unset = UNSET,
    session_id: None | str | Unset = UNSET,
    status: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | RunListResponse]:
    """List runs

     The org's run ledger, newest first.

    ``end_user_id`` takes the tenant's external identifier and resolves the
    surrogate internally — consistent with every response echoing only the
    external id. An unknown end user yields an empty page, not a 404: "no
    runs for this user" is an answer, not an error.

    Args:
        agent_id (None | str | Unset):
        end_user_id (None | str | Unset): The tenant's own end-user identifier
        session_id (None | str | Unset):
        status (None | str | Unset):
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RunListResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        end_user_id=end_user_id,
        session_id=session_id,
        status=status,
        limit=limit,
        offset=offset,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    agent_id: None | str | Unset = UNSET,
    end_user_id: None | str | Unset = UNSET,
    session_id: None | str | Unset = UNSET,
    status: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | RunListResponse | None:
    """List runs

     The org's run ledger, newest first.

    ``end_user_id`` takes the tenant's external identifier and resolves the
    surrogate internally — consistent with every response echoing only the
    external id. An unknown end user yields an empty page, not a 404: "no
    runs for this user" is an answer, not an error.

    Args:
        agent_id (None | str | Unset):
        end_user_id (None | str | Unset): The tenant's own end-user identifier
        session_id (None | str | Unset):
        status (None | str | Unset):
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RunListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            agent_id=agent_id,
            end_user_id=end_user_id,
            session_id=session_id,
            status=status,
            limit=limit,
            offset=offset,
            x_current_organization=x_current_organization,
        )
    ).parsed
