from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.file_response import FileResponse
from ...models.http_validation_error import HTTPValidationError
from typing import cast


def _get_kwargs(
    filename: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/files/{filename}".format(
            filename=quote(str(filename), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> FileResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = FileResponse.from_dict(response.json())

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
) -> Response[FileResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    filename: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[FileResponse | HTTPValidationError]:
    """Get file details

     Get details for a specific file.

    Returns the file metadata with a download URL.

    Args:
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FileResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        filename=filename,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    filename: str,
    *,
    client: AuthenticatedClient | Client,
) -> FileResponse | HTTPValidationError | None:
    """Get file details

     Get details for a specific file.

    Returns the file metadata with a download URL.

    Args:
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FileResponse | HTTPValidationError
    """

    return sync_detailed(
        filename=filename,
        client=client,
    ).parsed


async def asyncio_detailed(
    filename: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[FileResponse | HTTPValidationError]:
    """Get file details

     Get details for a specific file.

    Returns the file metadata with a download URL.

    Args:
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FileResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        filename=filename,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    filename: str,
    *,
    client: AuthenticatedClient | Client,
) -> FileResponse | HTTPValidationError | None:
    """Get file details

     Get details for a specific file.

    Returns the file metadata with a download URL.

    Args:
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FileResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            filename=filename,
            client=client,
        )
    ).parsed
