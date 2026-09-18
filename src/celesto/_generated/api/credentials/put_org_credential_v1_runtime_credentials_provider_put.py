from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.credential_response import CredentialResponse
from ...models.credential_upsert_request import CredentialUpsertRequest
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    provider: str,
    *,
    body: CredentialUpsertRequest,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/v1/runtime/credentials/{provider}".format(
            provider=quote(str(provider), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CredentialResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CredentialResponse.from_dict(response.json())

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
) -> Response[CredentialResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    provider: str,
    *,
    client: AuthenticatedClient | Client,
    body: CredentialUpsertRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[CredentialResponse | HTTPValidationError]:
    """Store the organization's credential for a provider

     Used by every end user who has no credential of their own — the B2B
    case, and the fallback in the B2B2C one.

    Args:
        provider (str):
        x_current_organization (str | Unset): Current organization ID
        body (CredentialUpsertRequest): Bring-your-own: the tenant supplies the credential,
            Celesto stores it.

            ``secret`` is shaped by ``auth_type``: ``{"api_key": "..."}`` or
            ``{"access_token": "..."}``. Refresh tokens and client secrets are refused
            — Celesto never performs a token exchange, so holding the durable half of
            a credential would add breach exposure for nothing.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        provider=provider,
        body=body,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    provider: str,
    *,
    client: AuthenticatedClient | Client,
    body: CredentialUpsertRequest,
    x_current_organization: str | Unset = UNSET,
) -> CredentialResponse | HTTPValidationError | None:
    """Store the organization's credential for a provider

     Used by every end user who has no credential of their own — the B2B
    case, and the fallback in the B2B2C one.

    Args:
        provider (str):
        x_current_organization (str | Unset): Current organization ID
        body (CredentialUpsertRequest): Bring-your-own: the tenant supplies the credential,
            Celesto stores it.

            ``secret`` is shaped by ``auth_type``: ``{"api_key": "..."}`` or
            ``{"access_token": "..."}``. Refresh tokens and client secrets are refused
            — Celesto never performs a token exchange, so holding the durable half of
            a credential would add breach exposure for nothing.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialResponse | HTTPValidationError
    """

    return sync_detailed(
        provider=provider,
        client=client,
        body=body,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    provider: str,
    *,
    client: AuthenticatedClient | Client,
    body: CredentialUpsertRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[CredentialResponse | HTTPValidationError]:
    """Store the organization's credential for a provider

     Used by every end user who has no credential of their own — the B2B
    case, and the fallback in the B2B2C one.

    Args:
        provider (str):
        x_current_organization (str | Unset): Current organization ID
        body (CredentialUpsertRequest): Bring-your-own: the tenant supplies the credential,
            Celesto stores it.

            ``secret`` is shaped by ``auth_type``: ``{"api_key": "..."}`` or
            ``{"access_token": "..."}``. Refresh tokens and client secrets are refused
            — Celesto never performs a token exchange, so holding the durable half of
            a credential would add breach exposure for nothing.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        provider=provider,
        body=body,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    provider: str,
    *,
    client: AuthenticatedClient | Client,
    body: CredentialUpsertRequest,
    x_current_organization: str | Unset = UNSET,
) -> CredentialResponse | HTTPValidationError | None:
    """Store the organization's credential for a provider

     Used by every end user who has no credential of their own — the B2B
    case, and the fallback in the B2B2C one.

    Args:
        provider (str):
        x_current_organization (str | Unset): Current organization ID
        body (CredentialUpsertRequest): Bring-your-own: the tenant supplies the credential,
            Celesto stores it.

            ``secret`` is shaped by ``auth_type``: ``{"api_key": "..."}`` or
            ``{"access_token": "..."}``. Refresh tokens and client secrets are refused
            — Celesto never performs a token exchange, so holding the durable half of
            a credential would add breach exposure for nothing.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            provider=provider,
            client=client,
            body=body,
            x_current_organization=x_current_organization,
        )
    ).parsed
