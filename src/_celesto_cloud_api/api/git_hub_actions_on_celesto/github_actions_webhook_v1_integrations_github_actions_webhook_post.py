from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.github_actions_webhook_v1_integrations_github_actions_webhook_post_response_github_actions_webhook_v1_integrations_github_actions_webhook_post import (
    GithubActionsWebhookV1IntegrationsGithubActionsWebhookPostResponseGithubActionsWebhookV1IntegrationsGithubActionsWebhookPost,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    x_hub_signature_256: None | str | Unset = UNSET,
    x_github_event: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_hub_signature_256, Unset):
        headers["x-hub-signature-256"] = x_hub_signature_256

    if not isinstance(x_github_event, Unset):
        headers["x-github-event"] = x_github_event

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/integrations/github/actions/webhook",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GithubActionsWebhookV1IntegrationsGithubActionsWebhookPostResponseGithubActionsWebhookV1IntegrationsGithubActionsWebhookPost
    | HTTPValidationError
    | None
):
    if response.status_code == 202:
        response_202 = GithubActionsWebhookV1IntegrationsGithubActionsWebhookPostResponseGithubActionsWebhookV1IntegrationsGithubActionsWebhookPost.from_dict(
            response.json()
        )

        return response_202

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
    GithubActionsWebhookV1IntegrationsGithubActionsWebhookPostResponseGithubActionsWebhookV1IntegrationsGithubActionsWebhookPost
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
    x_hub_signature_256: None | str | Unset = UNSET,
    x_github_event: None | str | Unset = UNSET,
) -> Response[
    GithubActionsWebhookV1IntegrationsGithubActionsWebhookPostResponseGithubActionsWebhookV1IntegrationsGithubActionsWebhookPost
    | HTTPValidationError
]:
    """Github Actions Webhook

    Args:
        x_hub_signature_256 (None | str | Unset):
        x_github_event (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GithubActionsWebhookV1IntegrationsGithubActionsWebhookPostResponseGithubActionsWebhookV1IntegrationsGithubActionsWebhookPost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        x_hub_signature_256=x_hub_signature_256,
        x_github_event=x_github_event,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    x_hub_signature_256: None | str | Unset = UNSET,
    x_github_event: None | str | Unset = UNSET,
) -> (
    GithubActionsWebhookV1IntegrationsGithubActionsWebhookPostResponseGithubActionsWebhookV1IntegrationsGithubActionsWebhookPost
    | HTTPValidationError
    | None
):
    """Github Actions Webhook

    Args:
        x_hub_signature_256 (None | str | Unset):
        x_github_event (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GithubActionsWebhookV1IntegrationsGithubActionsWebhookPostResponseGithubActionsWebhookV1IntegrationsGithubActionsWebhookPost | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        x_hub_signature_256=x_hub_signature_256,
        x_github_event=x_github_event,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    x_hub_signature_256: None | str | Unset = UNSET,
    x_github_event: None | str | Unset = UNSET,
) -> Response[
    GithubActionsWebhookV1IntegrationsGithubActionsWebhookPostResponseGithubActionsWebhookV1IntegrationsGithubActionsWebhookPost
    | HTTPValidationError
]:
    """Github Actions Webhook

    Args:
        x_hub_signature_256 (None | str | Unset):
        x_github_event (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GithubActionsWebhookV1IntegrationsGithubActionsWebhookPostResponseGithubActionsWebhookV1IntegrationsGithubActionsWebhookPost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        x_hub_signature_256=x_hub_signature_256,
        x_github_event=x_github_event,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    x_hub_signature_256: None | str | Unset = UNSET,
    x_github_event: None | str | Unset = UNSET,
) -> (
    GithubActionsWebhookV1IntegrationsGithubActionsWebhookPostResponseGithubActionsWebhookV1IntegrationsGithubActionsWebhookPost
    | HTTPValidationError
    | None
):
    """Github Actions Webhook

    Args:
        x_hub_signature_256 (None | str | Unset):
        x_github_event (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GithubActionsWebhookV1IntegrationsGithubActionsWebhookPostResponseGithubActionsWebhookV1IntegrationsGithubActionsWebhookPost | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            x_hub_signature_256=x_hub_signature_256,
            x_github_event=x_github_event,
        )
    ).parsed
