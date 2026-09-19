from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.git_hub_git_credential_request import GitHubGitCredentialRequest
from ...models.git_hub_git_credential_response import GitHubGitCredentialResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    workspace_id: str,
    *,
    body: GitHubGitCredentialRequest | None | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/internal/workspaces/{workspace_id}/github/git-credentials".format(
            workspace_id=quote(str(workspace_id), safe=""),
        ),
    }

    if isinstance(body, GitHubGitCredentialRequest):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GitHubGitCredentialResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = GitHubGitCredentialResponse.from_dict(response.json())

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
) -> Response[GitHubGitCredentialResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: GitHubGitCredentialRequest | None | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Response[GitHubGitCredentialResponse | HTTPValidationError]:
    """Return Git credentials to a trusted workspace runtime

    Args:
        workspace_id (str):
        authorization (None | str | Unset):
        body (GitHubGitCredentialRequest | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GitHubGitCredentialResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        body=body,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: GitHubGitCredentialRequest | None | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> GitHubGitCredentialResponse | HTTPValidationError | None:
    """Return Git credentials to a trusted workspace runtime

    Args:
        workspace_id (str):
        authorization (None | str | Unset):
        body (GitHubGitCredentialRequest | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GitHubGitCredentialResponse | HTTPValidationError
    """

    return sync_detailed(
        workspace_id=workspace_id,
        client=client,
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    workspace_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: GitHubGitCredentialRequest | None | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> Response[GitHubGitCredentialResponse | HTTPValidationError]:
    """Return Git credentials to a trusted workspace runtime

    Args:
        workspace_id (str):
        authorization (None | str | Unset):
        body (GitHubGitCredentialRequest | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GitHubGitCredentialResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        body=body,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: GitHubGitCredentialRequest | None | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
) -> GitHubGitCredentialResponse | HTTPValidationError | None:
    """Return Git credentials to a trusted workspace runtime

    Args:
        workspace_id (str):
        authorization (None | str | Unset):
        body (GitHubGitCredentialRequest | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GitHubGitCredentialResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            workspace_id=workspace_id,
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
