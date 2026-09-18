from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.model_provider import ModelProvider
from ...models.model_provider_connect_request import ModelProviderConnectRequest
from ...models.model_provider_connection_info import ModelProviderConnectionInfo
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    provider: ModelProvider,
    *,
    body: ModelProviderConnectRequest,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/v1/model-providers/{provider}".format(
            provider=quote(str(provider), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ModelProviderConnectionInfo | None:
    if response.status_code == 200:
        response_200 = ModelProviderConnectionInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | ModelProviderConnectionInfo]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    provider: ModelProvider,
    *,
    client: AuthenticatedClient | Client,
    body: ModelProviderConnectRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | ModelProviderConnectionInfo]:
    """Connect a provider or rotate its API key

     Store an encrypted API key for this organization.

    The key is checked against the provider first; a definitive rejection
    returns 422 and nothing is stored.

    Args:
        provider (ModelProvider): LLM providers users can connect their own credentials for.
        x_current_organization (str | Unset): Current organization ID
        body (ModelProviderConnectRequest): Connect or rotate the API key for a provider.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ModelProviderConnectionInfo]
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
    provider: ModelProvider,
    *,
    client: AuthenticatedClient | Client,
    body: ModelProviderConnectRequest,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | ModelProviderConnectionInfo | None:
    """Connect a provider or rotate its API key

     Store an encrypted API key for this organization.

    The key is checked against the provider first; a definitive rejection
    returns 422 and nothing is stored.

    Args:
        provider (ModelProvider): LLM providers users can connect their own credentials for.
        x_current_organization (str | Unset): Current organization ID
        body (ModelProviderConnectRequest): Connect or rotate the API key for a provider.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ModelProviderConnectionInfo
    """

    return sync_detailed(
        provider=provider,
        client=client,
        body=body,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    provider: ModelProvider,
    *,
    client: AuthenticatedClient | Client,
    body: ModelProviderConnectRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | ModelProviderConnectionInfo]:
    """Connect a provider or rotate its API key

     Store an encrypted API key for this organization.

    The key is checked against the provider first; a definitive rejection
    returns 422 and nothing is stored.

    Args:
        provider (ModelProvider): LLM providers users can connect their own credentials for.
        x_current_organization (str | Unset): Current organization ID
        body (ModelProviderConnectRequest): Connect or rotate the API key for a provider.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ModelProviderConnectionInfo]
    """

    kwargs = _get_kwargs(
        provider=provider,
        body=body,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    provider: ModelProvider,
    *,
    client: AuthenticatedClient | Client,
    body: ModelProviderConnectRequest,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | ModelProviderConnectionInfo | None:
    """Connect a provider or rotate its API key

     Store an encrypted API key for this organization.

    The key is checked against the provider first; a definitive rejection
    returns 422 and nothing is stored.

    Args:
        provider (ModelProvider): LLM providers users can connect their own credentials for.
        x_current_organization (str | Unset): Current organization ID
        body (ModelProviderConnectRequest): Connect or rotate the API key for a provider.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ModelProviderConnectionInfo
    """

    return (
        await asyncio_detailed(
            provider=provider,
            client=client,
            body=body,
            x_current_organization=x_current_organization,
        )
    ).parsed
