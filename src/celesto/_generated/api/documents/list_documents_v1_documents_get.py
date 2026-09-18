from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.document_list_response import DocumentListResponse
from ...models.document_scope import DocumentScope
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    skip: int | Unset = 0,
    limit: int | Unset = 10,
    search: None | str | Unset = UNSET,
    document_type: None | str | Unset = UNSET,
    tags: None | str | Unset = UNSET,
    scope: DocumentScope | Unset = UNSET,
    organization_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

    json_search: None | str | Unset
    if isinstance(search, Unset):
        json_search = UNSET
    else:
        json_search = search
    params["search"] = json_search

    json_document_type: None | str | Unset
    if isinstance(document_type, Unset):
        json_document_type = UNSET
    else:
        json_document_type = document_type
    params["document_type"] = json_document_type

    json_tags: None | str | Unset
    if isinstance(tags, Unset):
        json_tags = UNSET
    else:
        json_tags = tags
    params["tags"] = json_tags

    json_scope: str | Unset = UNSET
    if not isinstance(scope, Unset):
        json_scope = scope.value

    params["scope"] = json_scope

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
        "url": "/v1/documents",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DocumentListResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DocumentListResponse.from_dict(response.json())

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
) -> Response[DocumentListResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = 0,
    limit: int | Unset = 10,
    search: None | str | Unset = UNSET,
    document_type: None | str | Unset = UNSET,
    tags: None | str | Unset = UNSET,
    scope: DocumentScope | Unset = UNSET,
    organization_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
) -> Response[DocumentListResponse | HTTPValidationError]:
    """List documents

     List documents with flexible scope support.

    Supports three access patterns:
    1. Organization-level: scope=organization, organization_id=<id>
    2. Project-level: scope=project, project_id=<id>
    3. User-level: scope=user (uses personal organization)

    Args:
        skip (int | Unset): Skip the first N items Default: 0.
        limit (int | Unset): Limit the number of items returned Default: 10.
        search (None | str | Unset): Search term for title and description
        document_type (None | str | Unset): Filter by document type
        tags (None | str | Unset): Filter by tags (comma-separated)
        scope (DocumentScope | Unset): Document access scope
        organization_id (None | str | Unset): Organization ID (required for organization scope)
        project_id (None | str | Unset): Project ID (required for project scope)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DocumentListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        search=search,
        document_type=document_type,
        tags=tags,
        scope=scope,
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
    skip: int | Unset = 0,
    limit: int | Unset = 10,
    search: None | str | Unset = UNSET,
    document_type: None | str | Unset = UNSET,
    tags: None | str | Unset = UNSET,
    scope: DocumentScope | Unset = UNSET,
    organization_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
) -> DocumentListResponse | HTTPValidationError | None:
    """List documents

     List documents with flexible scope support.

    Supports three access patterns:
    1. Organization-level: scope=organization, organization_id=<id>
    2. Project-level: scope=project, project_id=<id>
    3. User-level: scope=user (uses personal organization)

    Args:
        skip (int | Unset): Skip the first N items Default: 0.
        limit (int | Unset): Limit the number of items returned Default: 10.
        search (None | str | Unset): Search term for title and description
        document_type (None | str | Unset): Filter by document type
        tags (None | str | Unset): Filter by tags (comma-separated)
        scope (DocumentScope | Unset): Document access scope
        organization_id (None | str | Unset): Organization ID (required for organization scope)
        project_id (None | str | Unset): Project ID (required for project scope)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DocumentListResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        search=search,
        document_type=document_type,
        tags=tags,
        scope=scope,
        organization_id=organization_id,
        project_id=project_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = 0,
    limit: int | Unset = 10,
    search: None | str | Unset = UNSET,
    document_type: None | str | Unset = UNSET,
    tags: None | str | Unset = UNSET,
    scope: DocumentScope | Unset = UNSET,
    organization_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
) -> Response[DocumentListResponse | HTTPValidationError]:
    """List documents

     List documents with flexible scope support.

    Supports three access patterns:
    1. Organization-level: scope=organization, organization_id=<id>
    2. Project-level: scope=project, project_id=<id>
    3. User-level: scope=user (uses personal organization)

    Args:
        skip (int | Unset): Skip the first N items Default: 0.
        limit (int | Unset): Limit the number of items returned Default: 10.
        search (None | str | Unset): Search term for title and description
        document_type (None | str | Unset): Filter by document type
        tags (None | str | Unset): Filter by tags (comma-separated)
        scope (DocumentScope | Unset): Document access scope
        organization_id (None | str | Unset): Organization ID (required for organization scope)
        project_id (None | str | Unset): Project ID (required for project scope)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DocumentListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        search=search,
        document_type=document_type,
        tags=tags,
        scope=scope,
        organization_id=organization_id,
        project_id=project_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = 0,
    limit: int | Unset = 10,
    search: None | str | Unset = UNSET,
    document_type: None | str | Unset = UNSET,
    tags: None | str | Unset = UNSET,
    scope: DocumentScope | Unset = UNSET,
    organization_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
) -> DocumentListResponse | HTTPValidationError | None:
    """List documents

     List documents with flexible scope support.

    Supports three access patterns:
    1. Organization-level: scope=organization, organization_id=<id>
    2. Project-level: scope=project, project_id=<id>
    3. User-level: scope=user (uses personal organization)

    Args:
        skip (int | Unset): Skip the first N items Default: 0.
        limit (int | Unset): Limit the number of items returned Default: 10.
        search (None | str | Unset): Search term for title and description
        document_type (None | str | Unset): Filter by document type
        tags (None | str | Unset): Filter by tags (comma-separated)
        scope (DocumentScope | Unset): Document access scope
        organization_id (None | str | Unset): Organization ID (required for organization scope)
        project_id (None | str | Unset): Project ID (required for project scope)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DocumentListResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            search=search,
            document_type=document_type,
            tags=tags,
            scope=scope,
            organization_id=organization_id,
            project_id=project_id,
        )
    ).parsed
