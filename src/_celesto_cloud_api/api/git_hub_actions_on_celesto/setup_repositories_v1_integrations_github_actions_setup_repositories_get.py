from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.setup_repositories_v1_integrations_github_actions_setup_repositories_get_response_setup_repositories_v1_integrations_github_actions_setup_repositories_get import (
    SetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGetResponseSetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGet,
)
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    installation_id: int,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    params: dict[str, Any] = {}

    params["installation_id"] = installation_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/integrations/github/actions/setup-repositories",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | SetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGetResponseSetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGet
    | None
):
    if response.status_code == 200:
        response_200 = SetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGetResponseSetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGet.from_dict(
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
    | SetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGetResponseSetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGet
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
    installation_id: int,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    HTTPValidationError
    | SetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGetResponseSetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGet
]:
    """Setup Repositories

    Args:
        installation_id (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGetResponseSetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGet]
    """

    kwargs = _get_kwargs(
        installation_id=installation_id,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    installation_id: int,
    x_current_organization: str | Unset = UNSET,
) -> (
    HTTPValidationError
    | SetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGetResponseSetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGet
    | None
):
    """Setup Repositories

    Args:
        installation_id (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGetResponseSetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGet
    """

    return sync_detailed(
        client=client,
        installation_id=installation_id,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    installation_id: int,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    HTTPValidationError
    | SetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGetResponseSetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGet
]:
    """Setup Repositories

    Args:
        installation_id (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGetResponseSetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGet]
    """

    kwargs = _get_kwargs(
        installation_id=installation_id,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    installation_id: int,
    x_current_organization: str | Unset = UNSET,
) -> (
    HTTPValidationError
    | SetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGetResponseSetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGet
    | None
):
    """Setup Repositories

    Args:
        installation_id (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGetResponseSetupRepositoriesV1IntegrationsGithubActionsSetupRepositoriesGet
    """

    return (
        await asyncio_detailed(
            client=client,
            installation_id=installation_id,
            x_current_organization=x_current_organization,
        )
    ).parsed
