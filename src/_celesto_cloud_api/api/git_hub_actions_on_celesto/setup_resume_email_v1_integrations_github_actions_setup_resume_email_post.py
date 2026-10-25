from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.setup_resume_email import SetupResumeEmail
from ...models.setup_resume_email_v1_integrations_github_actions_setup_resume_email_post_response_setup_resume_email_v1_integrations_github_actions_setup_resume_email_post import (
    SetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPostResponseSetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPost,
)
from typing import cast


def _get_kwargs(
    *,
    body: SetupResumeEmail,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/integrations/github/actions/setup-resume-email",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | SetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPostResponseSetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPost
    | None
):
    if response.status_code == 200:
        response_200 = SetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPostResponseSetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPost.from_dict(
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
    HTTPValidationError
    | SetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPostResponseSetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPost
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
    body: SetupResumeEmail,
) -> Response[
    HTTPValidationError
    | SetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPostResponseSetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPost
]:
    """Setup Resume Email

    Args:
        body (SetupResumeEmail):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPostResponseSetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPost]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: SetupResumeEmail,
) -> (
    HTTPValidationError
    | SetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPostResponseSetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPost
    | None
):
    """Setup Resume Email

    Args:
        body (SetupResumeEmail):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPostResponseSetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPost
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SetupResumeEmail,
) -> Response[
    HTTPValidationError
    | SetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPostResponseSetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPost
]:
    """Setup Resume Email

    Args:
        body (SetupResumeEmail):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPostResponseSetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPost]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: SetupResumeEmail,
) -> (
    HTTPValidationError
    | SetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPostResponseSetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPost
    | None
):
    """Setup Resume Email

    Args:
        body (SetupResumeEmail):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPostResponseSetupResumeEmailV1IntegrationsGithubActionsSetupResumeEmailPost
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
