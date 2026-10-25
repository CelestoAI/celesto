from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.block_request import BlockRequest
from ...models.block_url_v1_integrations_github_actions_cache_celesto_block_url_post_response_block_url_v1_integrations_github_actions_cache_celesto_block_url_post import (
    BlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPostResponseBlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPost,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    body: BlockRequest,
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
        "url": "/v1/integrations/github/actions/cache/celesto/block-url",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    BlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPostResponseBlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPost
    | HTTPValidationError
    | None
):
    if response.status_code == 200:
        response_200 = BlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPostResponseBlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPost.from_dict(
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
    BlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPostResponseBlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPost
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
    body: BlockRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> Response[
    BlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPostResponseBlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPost
    | HTTPValidationError
]:
    """Block Url

     Presigned PUT for one block of a large upload (Azure "Put Block").

    Args:
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (BlockRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPostResponseBlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPost | HTTPValidationError]
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
    body: BlockRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> (
    BlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPostResponseBlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPost
    | HTTPValidationError
    | None
):
    """Block Url

     Presigned PUT for one block of a large upload (Azure "Put Block").

    Args:
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (BlockRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPostResponseBlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPost | HTTPValidationError
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
    body: BlockRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> Response[
    BlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPostResponseBlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPost
    | HTTPValidationError
]:
    """Block Url

     Presigned PUT for one block of a large upload (Azure "Put Block").

    Args:
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (BlockRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPostResponseBlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPost | HTTPValidationError]
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
    body: BlockRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> (
    BlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPostResponseBlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPost
    | HTTPValidationError
    | None
):
    """Block Url

     Presigned PUT for one block of a large upload (Azure "Put Block").

    Args:
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (BlockRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPostResponseBlockUrlV1IntegrationsGithubActionsCacheCelestoBlockUrlPost | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            authorization=authorization,
            x_celesto_host_provider=x_celesto_host_provider,
        )
    ).parsed
