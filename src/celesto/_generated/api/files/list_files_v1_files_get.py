from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.file_list_response import FileListResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    skip: int | Unset = 0,
    limit: int | Unset = 10,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/files",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> FileListResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = FileListResponse.from_dict(response.json())

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
) -> Response[FileListResponse | HTTPValidationError]:
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
) -> Response[FileListResponse | HTTPValidationError]:
    """List files

     List files uploaded by the user.

    Returns a list of files with their metadata and download URLs.

    Args:
        skip (int | Unset): Skip the first N items Default: 0.
        limit (int | Unset): Limit the number of items returned Default: 10.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FileListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
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
) -> FileListResponse | HTTPValidationError | None:
    """List files

     List files uploaded by the user.

    Returns a list of files with their metadata and download URLs.

    Args:
        skip (int | Unset): Skip the first N items Default: 0.
        limit (int | Unset): Limit the number of items returned Default: 10.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FileListResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = 0,
    limit: int | Unset = 10,
) -> Response[FileListResponse | HTTPValidationError]:
    """List files

     List files uploaded by the user.

    Returns a list of files with their metadata and download URLs.

    Args:
        skip (int | Unset): Skip the first N items Default: 0.
        limit (int | Unset): Limit the number of items returned Default: 10.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FileListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = 0,
    limit: int | Unset = 10,
) -> FileListResponse | HTTPValidationError | None:
    """List files

     List files uploaded by the user.

    Returns a list of files with their metadata and download URLs.

    Args:
        skip (int | Unset): Skip the first N items Default: 0.
        limit (int | Unset): Limit the number of items returned Default: 10.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FileListResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
        )
    ).parsed
