from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.delegated_access_drive_list_response import (
    DelegatedAccessDriveListResponse,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    project_name: str,
    subject: str,
    page_size: int | Unset = 20,
    page_token: None | str | Unset = UNSET,
    folder_id: None | str | Unset = UNSET,
    query: None | str | Unset = UNSET,
    include_folders: bool | Unset = True,
    order_by: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    params: dict[str, Any] = {}

    params["project_name"] = project_name

    params["subject"] = subject

    params["page_size"] = page_size

    json_page_token: None | str | Unset
    if isinstance(page_token, Unset):
        json_page_token = UNSET
    else:
        json_page_token = page_token
    params["page_token"] = json_page_token

    json_folder_id: None | str | Unset
    if isinstance(folder_id, Unset):
        json_folder_id = UNSET
    else:
        json_folder_id = folder_id
    params["folder_id"] = json_folder_id

    json_query: None | str | Unset
    if isinstance(query, Unset):
        json_query = UNSET
    else:
        json_query = query
    params["query"] = json_query

    params["include_folders"] = include_folders

    json_order_by: None | str | Unset
    if isinstance(order_by, Unset):
        json_order_by = UNSET
    else:
        json_order_by = order_by
    params["order_by"] = json_order_by

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/gatekeeper/connectors/drive/files",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DelegatedAccessDriveListResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DelegatedAccessDriveListResponse.from_dict(response.json())

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
) -> Response[DelegatedAccessDriveListResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_name: str,
    subject: str,
    page_size: int | Unset = 20,
    page_token: None | str | Unset = UNSET,
    folder_id: None | str | Unset = UNSET,
    query: None | str | Unset = UNSET,
    include_folders: bool | Unset = True,
    order_by: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[DelegatedAccessDriveListResponse | HTTPValidationError]:
    """List Drive Files

     List Google Drive files for a delegated subject

    Args:
        project_name (str): Project name to scope the access
        subject (str): Subject identifier
        page_size (int | Unset): Number of files per page Default: 20.
        page_token (None | str | Unset): Page token from previous response
        folder_id (None | str | Unset): Folder ID to list. Defaults to root unless a query is
            provided.
        query (None | str | Unset): Google Drive search query (q parameter)
        include_folders (bool | Unset): Include folders in results Default: True.
        order_by (None | str | Unset): Google Drive orderBy parameter
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DelegatedAccessDriveListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        project_name=project_name,
        subject=subject,
        page_size=page_size,
        page_token=page_token,
        folder_id=folder_id,
        query=query,
        include_folders=include_folders,
        order_by=order_by,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    project_name: str,
    subject: str,
    page_size: int | Unset = 20,
    page_token: None | str | Unset = UNSET,
    folder_id: None | str | Unset = UNSET,
    query: None | str | Unset = UNSET,
    include_folders: bool | Unset = True,
    order_by: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> DelegatedAccessDriveListResponse | HTTPValidationError | None:
    """List Drive Files

     List Google Drive files for a delegated subject

    Args:
        project_name (str): Project name to scope the access
        subject (str): Subject identifier
        page_size (int | Unset): Number of files per page Default: 20.
        page_token (None | str | Unset): Page token from previous response
        folder_id (None | str | Unset): Folder ID to list. Defaults to root unless a query is
            provided.
        query (None | str | Unset): Google Drive search query (q parameter)
        include_folders (bool | Unset): Include folders in results Default: True.
        order_by (None | str | Unset): Google Drive orderBy parameter
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DelegatedAccessDriveListResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        project_name=project_name,
        subject=subject,
        page_size=page_size,
        page_token=page_token,
        folder_id=folder_id,
        query=query,
        include_folders=include_folders,
        order_by=order_by,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_name: str,
    subject: str,
    page_size: int | Unset = 20,
    page_token: None | str | Unset = UNSET,
    folder_id: None | str | Unset = UNSET,
    query: None | str | Unset = UNSET,
    include_folders: bool | Unset = True,
    order_by: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[DelegatedAccessDriveListResponse | HTTPValidationError]:
    """List Drive Files

     List Google Drive files for a delegated subject

    Args:
        project_name (str): Project name to scope the access
        subject (str): Subject identifier
        page_size (int | Unset): Number of files per page Default: 20.
        page_token (None | str | Unset): Page token from previous response
        folder_id (None | str | Unset): Folder ID to list. Defaults to root unless a query is
            provided.
        query (None | str | Unset): Google Drive search query (q parameter)
        include_folders (bool | Unset): Include folders in results Default: True.
        order_by (None | str | Unset): Google Drive orderBy parameter
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DelegatedAccessDriveListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        project_name=project_name,
        subject=subject,
        page_size=page_size,
        page_token=page_token,
        folder_id=folder_id,
        query=query,
        include_folders=include_folders,
        order_by=order_by,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    project_name: str,
    subject: str,
    page_size: int | Unset = 20,
    page_token: None | str | Unset = UNSET,
    folder_id: None | str | Unset = UNSET,
    query: None | str | Unset = UNSET,
    include_folders: bool | Unset = True,
    order_by: None | str | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> DelegatedAccessDriveListResponse | HTTPValidationError | None:
    """List Drive Files

     List Google Drive files for a delegated subject

    Args:
        project_name (str): Project name to scope the access
        subject (str): Subject identifier
        page_size (int | Unset): Number of files per page Default: 20.
        page_token (None | str | Unset): Page token from previous response
        folder_id (None | str | Unset): Folder ID to list. Defaults to root unless a query is
            provided.
        query (None | str | Unset): Google Drive search query (q parameter)
        include_folders (bool | Unset): Include folders in results Default: True.
        order_by (None | str | Unset): Google Drive orderBy parameter
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DelegatedAccessDriveListResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            project_name=project_name,
            subject=subject,
            page_size=page_size,
            page_token=page_token,
            folder_id=folder_id,
            query=query,
            include_folders=include_folders,
            order_by=order_by,
            x_current_organization=x_current_organization,
        )
    ).parsed
