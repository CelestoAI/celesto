from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.git_credentials_v1_internal_pool_hosts_host_id_github_git_credentials_post_response_git_credentials_v1_internal_pool_hosts_host_id_github_git_credentials_post import (
    GitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPostResponseGitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPost,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.pool_git_credential_request import PoolGitCredentialRequest
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    host_id: str,
    *,
    body: PoolGitCredentialRequest,
    authorization: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/internal/pool/hosts/{host_id}/github/git-credentials".format(
            host_id=quote(str(host_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPostResponseGitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPost
    | HTTPValidationError
    | None
):
    if response.status_code == 200:
        response_200 = GitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPostResponseGitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPost.from_dict(
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
    GitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPostResponseGitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPost
    | HTTPValidationError
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PoolGitCredentialRequest,
    authorization: None | str | Unset = UNSET,
) -> Response[
    GitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPostResponseGitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPost
    | HTTPValidationError
]:
    """Git Credentials

    Args:
        host_id (str):
        authorization (None | str | Unset):
        body (PoolGitCredentialRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPostResponseGitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        body=body,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PoolGitCredentialRequest,
    authorization: None | str | Unset = UNSET,
) -> (
    GitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPostResponseGitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPost
    | HTTPValidationError
    | None
):
    """Git Credentials

    Args:
        host_id (str):
        authorization (None | str | Unset):
        body (PoolGitCredentialRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPostResponseGitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPost | HTTPValidationError
    """

    return sync_detailed(
        host_id=host_id,
        client=client,
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PoolGitCredentialRequest,
    authorization: None | str | Unset = UNSET,
) -> Response[
    GitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPostResponseGitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPost
    | HTTPValidationError
]:
    """Git Credentials

    Args:
        host_id (str):
        authorization (None | str | Unset):
        body (PoolGitCredentialRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPostResponseGitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        body=body,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PoolGitCredentialRequest,
    authorization: None | str | Unset = UNSET,
) -> (
    GitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPostResponseGitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPost
    | HTTPValidationError
    | None
):
    """Git Credentials

    Args:
        host_id (str):
        authorization (None | str | Unset):
        body (PoolGitCredentialRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPostResponseGitCredentialsV1InternalPoolHostsHostIdGithubGitCredentialsPost | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            host_id=host_id,
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
