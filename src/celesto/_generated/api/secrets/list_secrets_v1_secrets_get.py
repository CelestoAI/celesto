from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.secret_list_response import SecretListResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    search: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    organization_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_search: None | str | Unset
    if isinstance(search, Unset):
        json_search = UNSET
    else:
        json_search = search
    params["search"] = json_search

    params["limit"] = limit

    json_organization_id: None | str | Unset
    if isinstance(organization_id, Unset):
        json_organization_id = UNSET
    else:
        json_organization_id = organization_id
    params["organization_id"] = json_organization_id

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/secrets",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | SecretListResponse | None:
    if response.status_code == 200:
        response_200 = SecretListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | SecretListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    search: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    organization_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | SecretListResponse]:
    """List secrets

     List org-level secrets + current project secrets. Values are always masked.

    Args:
        search (None | str | Unset):
        limit (int | Unset):  Default: 50.
        organization_id (None | str | Unset):
        project_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SecretListResponse]
    """

    kwargs = _get_kwargs(
        search=search,
        limit=limit,
        organization_id=organization_id,
        project_id=project_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    search: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    organization_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
) -> HTTPValidationError | SecretListResponse | None:
    """List secrets

     List org-level secrets + current project secrets. Values are always masked.

    Args:
        search (None | str | Unset):
        limit (int | Unset):  Default: 50.
        organization_id (None | str | Unset):
        project_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SecretListResponse
    """

    return sync_detailed(
        client=client,
        search=search,
        limit=limit,
        organization_id=organization_id,
        project_id=project_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    search: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    organization_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | SecretListResponse]:
    """List secrets

     List org-level secrets + current project secrets. Values are always masked.

    Args:
        search (None | str | Unset):
        limit (int | Unset):  Default: 50.
        organization_id (None | str | Unset):
        project_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SecretListResponse]
    """

    kwargs = _get_kwargs(
        search=search,
        limit=limit,
        organization_id=organization_id,
        project_id=project_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    search: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    organization_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
) -> HTTPValidationError | SecretListResponse | None:
    """List secrets

     List org-level secrets + current project secrets. Values are always masked.

    Args:
        search (None | str | Unset):
        limit (int | Unset):  Default: 50.
        organization_id (None | str | Unset):
        project_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SecretListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            search=search,
            limit=limit,
            organization_id=organization_id,
            project_id=project_id,
        )
    ).parsed
