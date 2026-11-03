from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.list_runners_v1_integrations_github_actions_runners_get_response_list_runners_v1_integrations_github_actions_runners_get import (
    ListRunnersV1IntegrationsGithubActionsRunnersGetResponseListRunnersV1IntegrationsGithubActionsRunnersGet,
)
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/integrations/github/actions/runners",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | ListRunnersV1IntegrationsGithubActionsRunnersGetResponseListRunnersV1IntegrationsGithubActionsRunnersGet
    | None
):
    if response.status_code == 200:
        response_200 = ListRunnersV1IntegrationsGithubActionsRunnersGetResponseListRunnersV1IntegrationsGithubActionsRunnersGet.from_dict(
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
    | ListRunnersV1IntegrationsGithubActionsRunnersGetResponseListRunnersV1IntegrationsGithubActionsRunnersGet
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
    x_current_organization: str | Unset = UNSET,
) -> Response[
    HTTPValidationError
    | ListRunnersV1IntegrationsGithubActionsRunnersGetResponseListRunnersV1IntegrationsGithubActionsRunnersGet
]:
    """List Runners

     The machine sizes a workflow can ask for with `runs-on`, in documented order.

    Args:
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ListRunnersV1IntegrationsGithubActionsRunnersGetResponseListRunnersV1IntegrationsGithubActionsRunnersGet]
    """

    kwargs = _get_kwargs(
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> (
    HTTPValidationError
    | ListRunnersV1IntegrationsGithubActionsRunnersGetResponseListRunnersV1IntegrationsGithubActionsRunnersGet
    | None
):
    """List Runners

     The machine sizes a workflow can ask for with `runs-on`, in documented order.

    Args:
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ListRunnersV1IntegrationsGithubActionsRunnersGetResponseListRunnersV1IntegrationsGithubActionsRunnersGet
    """

    return sync_detailed(
        client=client,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    HTTPValidationError
    | ListRunnersV1IntegrationsGithubActionsRunnersGetResponseListRunnersV1IntegrationsGithubActionsRunnersGet
]:
    """List Runners

     The machine sizes a workflow can ask for with `runs-on`, in documented order.

    Args:
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ListRunnersV1IntegrationsGithubActionsRunnersGetResponseListRunnersV1IntegrationsGithubActionsRunnersGet]
    """

    kwargs = _get_kwargs(
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> (
    HTTPValidationError
    | ListRunnersV1IntegrationsGithubActionsRunnersGetResponseListRunnersV1IntegrationsGithubActionsRunnersGet
    | None
):
    """List Runners

     The machine sizes a workflow can ask for with `runs-on`, in documented order.

    Args:
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ListRunnersV1IntegrationsGithubActionsRunnersGetResponseListRunnersV1IntegrationsGithubActionsRunnersGet
    """

    return (
        await asyncio_detailed(
            client=client,
            x_current_organization=x_current_organization,
        )
    ).parsed
