from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.thread_list_response import ThreadListResponse
from ...models.thread_status import ThreadStatus
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    project_id: None | str | Unset = UNSET,
    organization_id: None | str | Unset = UNSET,
    agent_id: None | str | Unset = UNSET,
    subject: None | str | Unset = UNSET,
    status: None | ThreadStatus | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    json_organization_id: None | str | Unset
    if isinstance(organization_id, Unset):
        json_organization_id = UNSET
    else:
        json_organization_id = organization_id
    params["organization_id"] = json_organization_id

    json_agent_id: None | str | Unset
    if isinstance(agent_id, Unset):
        json_agent_id = UNSET
    else:
        json_agent_id = agent_id
    params["agent_id"] = json_agent_id

    json_subject: None | str | Unset
    if isinstance(subject, Unset):
        json_subject = UNSET
    else:
        json_subject = subject
    params["subject"] = json_subject

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, ThreadStatus):
        json_status = status.value
    else:
        json_status = status
    params["status"] = json_status

    params["limit"] = limit

    params["offset"] = offset

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/threads",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ThreadListResponse | None:
    if response.status_code == 200:
        response_200 = ThreadListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | ThreadListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_id: None | str | Unset = UNSET,
    organization_id: None | str | Unset = UNSET,
    agent_id: None | str | Unset = UNSET,
    subject: None | str | Unset = UNSET,
    status: None | ThreadStatus | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> Response[HTTPValidationError | ThreadListResponse]:
    """List conversation threads

     List threads, most recently active first.

    Args:
        project_id (None | str | Unset): Project to list threads from
        organization_id (None | str | Unset): Organization; uses its default project
        agent_id (None | str | Unset): Only threads bound to this agent
        subject (None | str | Unset): Only threads for this end user
        status (None | ThreadStatus | Unset):
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ThreadListResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        organization_id=organization_id,
        agent_id=agent_id,
        subject=subject,
        status=status,
        limit=limit,
        offset=offset,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    project_id: None | str | Unset = UNSET,
    organization_id: None | str | Unset = UNSET,
    agent_id: None | str | Unset = UNSET,
    subject: None | str | Unset = UNSET,
    status: None | ThreadStatus | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> HTTPValidationError | ThreadListResponse | None:
    """List conversation threads

     List threads, most recently active first.

    Args:
        project_id (None | str | Unset): Project to list threads from
        organization_id (None | str | Unset): Organization; uses its default project
        agent_id (None | str | Unset): Only threads bound to this agent
        subject (None | str | Unset): Only threads for this end user
        status (None | ThreadStatus | Unset):
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ThreadListResponse
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        organization_id=organization_id,
        agent_id=agent_id,
        subject=subject,
        status=status,
        limit=limit,
        offset=offset,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_id: None | str | Unset = UNSET,
    organization_id: None | str | Unset = UNSET,
    agent_id: None | str | Unset = UNSET,
    subject: None | str | Unset = UNSET,
    status: None | ThreadStatus | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> Response[HTTPValidationError | ThreadListResponse]:
    """List conversation threads

     List threads, most recently active first.

    Args:
        project_id (None | str | Unset): Project to list threads from
        organization_id (None | str | Unset): Organization; uses its default project
        agent_id (None | str | Unset): Only threads bound to this agent
        subject (None | str | Unset): Only threads for this end user
        status (None | ThreadStatus | Unset):
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ThreadListResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        organization_id=organization_id,
        agent_id=agent_id,
        subject=subject,
        status=status,
        limit=limit,
        offset=offset,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    project_id: None | str | Unset = UNSET,
    organization_id: None | str | Unset = UNSET,
    agent_id: None | str | Unset = UNSET,
    subject: None | str | Unset = UNSET,
    status: None | ThreadStatus | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> HTTPValidationError | ThreadListResponse | None:
    """List conversation threads

     List threads, most recently active first.

    Args:
        project_id (None | str | Unset): Project to list threads from
        organization_id (None | str | Unset): Organization; uses its default project
        agent_id (None | str | Unset): Only threads bound to this agent
        subject (None | str | Unset): Only threads for this end user
        status (None | ThreadStatus | Unset):
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ThreadListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            organization_id=organization_id,
            agent_id=agent_id,
            subject=subject,
            status=status,
            limit=limit,
            offset=offset,
        )
    ).parsed
