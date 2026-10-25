from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.authorize_installation import AuthorizeInstallation
from ...models.authorize_url_v1_integrations_github_actions_authorize_url_post_response_authorize_url_v1_integrations_github_actions_authorize_url_post import (
    AuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPostResponseAuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPost,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    body: AuthorizeInstallation,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/integrations/github/actions/authorize-url",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    AuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPostResponseAuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPost
    | HTTPValidationError
    | None
):
    if response.status_code == 200:
        response_200 = AuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPostResponseAuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPost.from_dict(
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
    AuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPostResponseAuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPost
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
    body: AuthorizeInstallation,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    AuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPostResponseAuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPost
    | HTTPValidationError
]:
    """Authorize Url

     Start the Celesto CI App's own user authorization (D-03).

    The signed-in request records who is proving admin for which installation,
    so the callback can tie GitHub's answer to this Celesto user.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (AuthorizeInstallation):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPostResponseAuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: AuthorizeInstallation,
    x_current_organization: str | Unset = UNSET,
) -> (
    AuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPostResponseAuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPost
    | HTTPValidationError
    | None
):
    """Authorize Url

     Start the Celesto CI App's own user authorization (D-03).

    The signed-in request records who is proving admin for which installation,
    so the callback can tie GitHub's answer to this Celesto user.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (AuthorizeInstallation):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPostResponseAuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPost | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AuthorizeInstallation,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    AuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPostResponseAuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPost
    | HTTPValidationError
]:
    """Authorize Url

     Start the Celesto CI App's own user authorization (D-03).

    The signed-in request records who is proving admin for which installation,
    so the callback can tie GitHub's answer to this Celesto user.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (AuthorizeInstallation):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPostResponseAuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: AuthorizeInstallation,
    x_current_organization: str | Unset = UNSET,
) -> (
    AuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPostResponseAuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPost
    | HTTPValidationError
    | None
):
    """Authorize Url

     Start the Celesto CI App's own user authorization (D-03).

    The signed-in request records who is proving admin for which installation,
    so the callback can tie GitHub's answer to this Celesto user.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (AuthorizeInstallation):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPostResponseAuthorizeUrlV1IntegrationsGithubActionsAuthorizeUrlPost | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_current_organization=x_current_organization,
        )
    ).parsed
