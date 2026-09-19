from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.secret_delete_response import SecretDeleteResponse
from typing import cast


def _get_kwargs(
    secret_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/v1/secrets/{secret_id}".format(
            secret_id=quote(str(secret_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | SecretDeleteResponse | None:
    if response.status_code == 200:
        response_200 = SecretDeleteResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | SecretDeleteResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    secret_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | SecretDeleteResponse]:
    """Delete a secret

     Soft delete a secret. Can be recovered by admins if needed.

    Args:
        secret_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SecretDeleteResponse]
    """

    kwargs = _get_kwargs(
        secret_id=secret_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    secret_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | SecretDeleteResponse | None:
    """Delete a secret

     Soft delete a secret. Can be recovered by admins if needed.

    Args:
        secret_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SecretDeleteResponse
    """

    return sync_detailed(
        secret_id=secret_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    secret_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | SecretDeleteResponse]:
    """Delete a secret

     Soft delete a secret. Can be recovered by admins if needed.

    Args:
        secret_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SecretDeleteResponse]
    """

    kwargs = _get_kwargs(
        secret_id=secret_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    secret_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | SecretDeleteResponse | None:
    """Delete a secret

     Soft delete a secret. Can be recovered by admins if needed.

    Args:
        secret_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SecretDeleteResponse
    """

    return (
        await asyncio_detailed(
            secret_id=secret_id,
            client=client,
        )
    ).parsed
