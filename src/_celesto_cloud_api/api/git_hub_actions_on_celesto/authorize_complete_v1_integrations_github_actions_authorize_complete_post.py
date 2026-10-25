from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.authorize_complete_v1_integrations_github_actions_authorize_complete_post_response_authorize_complete_v1_integrations_github_actions_authorize_complete_post import (
    AuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePostResponseAuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePost,
)
from ...models.complete_authorization import CompleteAuthorization
from ...models.http_validation_error import HTTPValidationError
from typing import cast


def _get_kwargs(
    *,
    body: CompleteAuthorization,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/integrations/github/actions/authorize-complete",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    AuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePostResponseAuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePost
    | HTTPValidationError
    | None
):
    if response.status_code == 200:
        response_200 = AuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePostResponseAuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePost.from_dict(
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
    AuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePostResponseAuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePost
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
    body: CompleteAuthorization,
) -> Response[
    AuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePostResponseAuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePost
    | HTTPValidationError
]:
    """Authorize Complete

     Finish authorization from the signed-in setup page (D-10).

    The state is used once. Only the Celesto user who started the flow may
    finish it, so a GitHub admin tricked into opening someone else's link
    cannot hand over their proof. The user token proves admin and is dropped;
    only the verdict is kept (D-04, D-05).

    Args:
        body (CompleteAuthorization):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePostResponseAuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePost | HTTPValidationError]
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
    body: CompleteAuthorization,
) -> (
    AuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePostResponseAuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePost
    | HTTPValidationError
    | None
):
    """Authorize Complete

     Finish authorization from the signed-in setup page (D-10).

    The state is used once. Only the Celesto user who started the flow may
    finish it, so a GitHub admin tricked into opening someone else's link
    cannot hand over their proof. The user token proves admin and is dropped;
    only the verdict is kept (D-04, D-05).

    Args:
        body (CompleteAuthorization):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePostResponseAuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePost | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CompleteAuthorization,
) -> Response[
    AuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePostResponseAuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePost
    | HTTPValidationError
]:
    """Authorize Complete

     Finish authorization from the signed-in setup page (D-10).

    The state is used once. Only the Celesto user who started the flow may
    finish it, so a GitHub admin tricked into opening someone else's link
    cannot hand over their proof. The user token proves admin and is dropped;
    only the verdict is kept (D-04, D-05).

    Args:
        body (CompleteAuthorization):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePostResponseAuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CompleteAuthorization,
) -> (
    AuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePostResponseAuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePost
    | HTTPValidationError
    | None
):
    """Authorize Complete

     Finish authorization from the signed-in setup page (D-10).

    The state is used once. Only the Celesto user who started the flow may
    finish it, so a GitHub admin tricked into opening someone else's link
    cannot hand over their proof. The user token proves admin and is dropped;
    only the verdict is kept (D-04, D-05).

    Args:
        body (CompleteAuthorization):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePostResponseAuthorizeCompleteV1IntegrationsGithubActionsAuthorizeCompletePost | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
