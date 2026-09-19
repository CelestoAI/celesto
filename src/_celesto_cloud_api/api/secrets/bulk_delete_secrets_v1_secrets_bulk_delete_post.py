from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.secret_bulk_delete_request import SecretBulkDeleteRequest
from ...models.secret_bulk_delete_response import SecretBulkDeleteResponse
from typing import cast


def _get_kwargs(
    *,
    body: SecretBulkDeleteRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/secrets/bulk-delete",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | SecretBulkDeleteResponse | None:
    if response.status_code == 200:
        response_200 = SecretBulkDeleteResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | SecretBulkDeleteResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SecretBulkDeleteRequest,
) -> Response[HTTPValidationError | SecretBulkDeleteResponse]:
    """Delete multiple secrets

     Soft delete multiple secrets in one request. Inaccessible or already-deleted secrets are skipped.

    Args:
        body (SecretBulkDeleteRequest): Request body for deleting multiple secrets.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SecretBulkDeleteResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: SecretBulkDeleteRequest,
) -> HTTPValidationError | SecretBulkDeleteResponse | None:
    """Delete multiple secrets

     Soft delete multiple secrets in one request. Inaccessible or already-deleted secrets are skipped.

    Args:
        body (SecretBulkDeleteRequest): Request body for deleting multiple secrets.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SecretBulkDeleteResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SecretBulkDeleteRequest,
) -> Response[HTTPValidationError | SecretBulkDeleteResponse]:
    """Delete multiple secrets

     Soft delete multiple secrets in one request. Inaccessible or already-deleted secrets are skipped.

    Args:
        body (SecretBulkDeleteRequest): Request body for deleting multiple secrets.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SecretBulkDeleteResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: SecretBulkDeleteRequest,
) -> HTTPValidationError | SecretBulkDeleteResponse | None:
    """Delete multiple secrets

     Soft delete multiple secrets in one request. Inaccessible or already-deleted secrets are skipped.

    Args:
        body (SecretBulkDeleteRequest): Request body for deleting multiple secrets.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SecretBulkDeleteResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
