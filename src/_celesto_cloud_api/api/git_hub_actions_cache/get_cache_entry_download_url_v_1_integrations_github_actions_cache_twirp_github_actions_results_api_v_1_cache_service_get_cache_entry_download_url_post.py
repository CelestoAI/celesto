from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.github_actions_cache_get_download_url_response import (
    GithubActionsCacheGetDownloadUrlResponse,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.lookup_request import LookupRequest
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    body: LookupRequest,
    x_celesto_ranged_download: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_celesto_ranged_download, Unset):
        headers["x-celesto-ranged-download"] = x_celesto_ranged_download

    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    if not isinstance(x_celesto_host_provider, Unset):
        headers["x-celesto-host-provider"] = x_celesto_host_provider

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/integrations/github/actions/cache/twirp/github.actions.results.api.v1.CacheService/GetCacheEntryDownloadURL",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GithubActionsCacheGetDownloadUrlResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = GithubActionsCacheGetDownloadUrlResponse.from_dict(
            response.json()
        )

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
) -> Response[GithubActionsCacheGetDownloadUrlResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: LookupRequest,
    x_celesto_ranged_download: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> Response[GithubActionsCacheGetDownloadUrlResponse | HTTPValidationError]:
    """Get Cache Entry Download Url

    Args:
        x_celesto_ranged_download (None | str | Unset):
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (LookupRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GithubActionsCacheGetDownloadUrlResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        x_celesto_ranged_download=x_celesto_ranged_download,
        authorization=authorization,
        x_celesto_host_provider=x_celesto_host_provider,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: LookupRequest,
    x_celesto_ranged_download: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> GithubActionsCacheGetDownloadUrlResponse | HTTPValidationError | None:
    """Get Cache Entry Download Url

    Args:
        x_celesto_ranged_download (None | str | Unset):
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (LookupRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GithubActionsCacheGetDownloadUrlResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
        x_celesto_ranged_download=x_celesto_ranged_download,
        authorization=authorization,
        x_celesto_host_provider=x_celesto_host_provider,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: LookupRequest,
    x_celesto_ranged_download: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> Response[GithubActionsCacheGetDownloadUrlResponse | HTTPValidationError]:
    """Get Cache Entry Download Url

    Args:
        x_celesto_ranged_download (None | str | Unset):
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (LookupRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GithubActionsCacheGetDownloadUrlResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        x_celesto_ranged_download=x_celesto_ranged_download,
        authorization=authorization,
        x_celesto_host_provider=x_celesto_host_provider,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: LookupRequest,
    x_celesto_ranged_download: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> GithubActionsCacheGetDownloadUrlResponse | HTTPValidationError | None:
    """Get Cache Entry Download Url

    Args:
        x_celesto_ranged_download (None | str | Unset):
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (LookupRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GithubActionsCacheGetDownloadUrlResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_celesto_ranged_download=x_celesto_ranged_download,
            authorization=authorization,
            x_celesto_host_provider=x_celesto_host_provider,
        )
    ).parsed
