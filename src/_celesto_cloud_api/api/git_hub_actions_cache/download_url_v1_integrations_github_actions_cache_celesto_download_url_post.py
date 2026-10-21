from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.download_url_request import DownloadUrlRequest
from ...models.download_url_v1_integrations_github_actions_cache_celesto_download_url_post_response_download_url_v1_integrations_github_actions_cache_celesto_download_url_post import (
    DownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPostResponseDownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPost,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    body: DownloadUrlRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    if not isinstance(x_celesto_host_provider, Unset):
        headers["x-celesto-host-provider"] = x_celesto_host_provider

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/integrations/github/actions/cache/celesto/download-url",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    DownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPostResponseDownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPost
    | HTTPValidationError
    | None
):
    if response.status_code == 200:
        response_200 = DownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPostResponseDownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPost.from_dict(
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
) -> Response[
    DownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPostResponseDownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPost
    | HTTPValidationError
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DownloadUrlRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> Response[
    DownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPostResponseDownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPost
    | HTTPValidationError
]:
    """Download Url

     Fresh presigned GET for an entry this job already looked up, so a long ranged download outlives one
    link (D-31).

    A refusal is ``{"url": "", "expiresIn": 0}``.

    Args:
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (DownloadUrlRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPostResponseDownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
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
    body: DownloadUrlRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> (
    DownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPostResponseDownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPost
    | HTTPValidationError
    | None
):
    """Download Url

     Fresh presigned GET for an entry this job already looked up, so a long ranged download outlives one
    link (D-31).

    A refusal is ``{"url": "", "expiresIn": 0}``.

    Args:
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (DownloadUrlRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPostResponseDownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPost | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
        authorization=authorization,
        x_celesto_host_provider=x_celesto_host_provider,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DownloadUrlRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> Response[
    DownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPostResponseDownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPost
    | HTTPValidationError
]:
    """Download Url

     Fresh presigned GET for an entry this job already looked up, so a long ranged download outlives one
    link (D-31).

    A refusal is ``{"url": "", "expiresIn": 0}``.

    Args:
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (DownloadUrlRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPostResponseDownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        authorization=authorization,
        x_celesto_host_provider=x_celesto_host_provider,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: DownloadUrlRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> (
    DownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPostResponseDownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPost
    | HTTPValidationError
    | None
):
    """Download Url

     Fresh presigned GET for an entry this job already looked up, so a long ranged download outlives one
    link (D-31).

    A refusal is ``{"url": "", "expiresIn": 0}``.

    Args:
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (DownloadUrlRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPostResponseDownloadUrlV1IntegrationsGithubActionsCacheCelestoDownloadUrlPost | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            authorization=authorization,
            x_celesto_host_provider=x_celesto_host_provider,
        )
    ).parsed
