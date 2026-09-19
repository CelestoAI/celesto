from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.agent_builder_list_response import AgentBuilderListResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    project_id: None | str | Unset = UNSET,
    organization_id: None | str | Unset = UNSET,
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

    params["limit"] = limit

    params["offset"] = offset

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/builder",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AgentBuilderListResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AgentBuilderListResponse.from_dict(response.json())

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
) -> Response[AgentBuilderListResponse | HTTPValidationError]:
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
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> Response[AgentBuilderListResponse | HTTPValidationError]:
    """List agent configs

     List agent configs for a project.

    Args:
        project_id (None | str | Unset): Project ID (preferred - agents are project-scoped)
        organization_id (None | str | Unset): Organization ID (for backward compatibility)
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentBuilderListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        organization_id=organization_id,
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
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> AgentBuilderListResponse | HTTPValidationError | None:
    """List agent configs

     List agent configs for a project.

    Args:
        project_id (None | str | Unset): Project ID (preferred - agents are project-scoped)
        organization_id (None | str | Unset): Organization ID (for backward compatibility)
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentBuilderListResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        organization_id=organization_id,
        limit=limit,
        offset=offset,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_id: None | str | Unset = UNSET,
    organization_id: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> Response[AgentBuilderListResponse | HTTPValidationError]:
    """List agent configs

     List agent configs for a project.

    Args:
        project_id (None | str | Unset): Project ID (preferred - agents are project-scoped)
        organization_id (None | str | Unset): Organization ID (for backward compatibility)
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentBuilderListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        organization_id=organization_id,
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
    limit: int | Unset = 50,
    offset: int | Unset = 0,
) -> AgentBuilderListResponse | HTTPValidationError | None:
    """List agent configs

     List agent configs for a project.

    Args:
        project_id (None | str | Unset): Project ID (preferred - agents are project-scoped)
        organization_id (None | str | Unset): Organization ID (for backward compatibility)
        limit (int | Unset):  Default: 50.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentBuilderListResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            organization_id=organization_id,
            limit=limit,
            offset=offset,
        )
    ).parsed
