from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.commit_blocks_request import CommitBlocksRequest
from ...models.commit_blocks_v1_integrations_github_actions_cache_celesto_commit_blocks_post_response_commit_blocks_v1_integrations_github_actions_cache_celesto_commit_blocks_post import (
    CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    body: CommitBlocksRequest,
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
        "url": "/v1/integrations/github/actions/cache/celesto/commit-blocks",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost
    | HTTPValidationError
    | None
):
    if response.status_code == 200:
        response_200 = CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost.from_dict(
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
    CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost
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
    body: CommitBlocksRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> Response[
    CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost
    | HTTPValidationError
]:
    """Commit Blocks

     Assemble uploaded blocks in Block List order (Azure "Put Block List"). Can take tens of seconds for
    large archives.

    Args:
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (CommitBlocksRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost | HTTPValidationError]
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
    body: CommitBlocksRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> (
    CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost
    | HTTPValidationError
    | None
):
    """Commit Blocks

     Assemble uploaded blocks in Block List order (Azure "Put Block List"). Can take tens of seconds for
    large archives.

    Args:
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (CommitBlocksRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost | HTTPValidationError
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
    body: CommitBlocksRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> Response[
    CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost
    | HTTPValidationError
]:
    """Commit Blocks

     Assemble uploaded blocks in Block List order (Azure "Put Block List"). Can take tens of seconds for
    large archives.

    Args:
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (CommitBlocksRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost | HTTPValidationError]
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
    body: CommitBlocksRequest,
    authorization: None | str | Unset = UNSET,
    x_celesto_host_provider: None | str | Unset = UNSET,
) -> (
    CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost
    | HTTPValidationError
    | None
):
    """Commit Blocks

     Assemble uploaded blocks in Block List order (Azure "Put Block List"). Can take tens of seconds for
    large archives.

    Args:
        authorization (None | str | Unset):
        x_celesto_host_provider (None | str | Unset):
        body (CommitBlocksRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            authorization=authorization,
            x_celesto_host_provider=x_celesto_host_provider,
        )
    ).parsed
