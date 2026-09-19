from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.secret_audit_response import SecretAuditResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    secret_id: str,
    *,
    limit: int | Unset = 50,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/secrets/{secret_id}/audit".format(
            secret_id=quote(str(secret_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | SecretAuditResponse | None:
    if response.status_code == 200:
        response_200 = SecretAuditResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | SecretAuditResponse]:
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
    limit: int | Unset = 50,
) -> Response[HTTPValidationError | SecretAuditResponse]:
    """Get audit trail

     Get audit trail for a secret including all operations.

    Args:
        secret_id (str):
        limit (int | Unset):  Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SecretAuditResponse]
    """

    kwargs = _get_kwargs(
        secret_id=secret_id,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    secret_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
) -> HTTPValidationError | SecretAuditResponse | None:
    """Get audit trail

     Get audit trail for a secret including all operations.

    Args:
        secret_id (str):
        limit (int | Unset):  Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SecretAuditResponse
    """

    return sync_detailed(
        secret_id=secret_id,
        client=client,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    secret_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
) -> Response[HTTPValidationError | SecretAuditResponse]:
    """Get audit trail

     Get audit trail for a secret including all operations.

    Args:
        secret_id (str):
        limit (int | Unset):  Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SecretAuditResponse]
    """

    kwargs = _get_kwargs(
        secret_id=secret_id,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    secret_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
) -> HTTPValidationError | SecretAuditResponse | None:
    """Get audit trail

     Get audit trail for a secret including all operations.

    Args:
        secret_id (str):
        limit (int | Unset):  Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SecretAuditResponse
    """

    return (
        await asyncio_detailed(
            secret_id=secret_id,
            client=client,
            limit=limit,
        )
    ).parsed
