from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.job_details_v1_integrations_github_actions_jobs_job_id_get_response_job_details_v1_integrations_github_actions_jobs_job_id_get import (
    JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet,
)
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    job_id: int,
    *,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/integrations/github/actions/jobs/{job_id}".format(
            job_id=quote(str(job_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet
    | None
):
    if response.status_code == 200:
        response_200 = JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet.from_dict(
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
    | JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    job_id: int,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    HTTPValidationError
    | JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet
]:
    """Job Details

    Args:
        job_id (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    job_id: int,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> (
    HTTPValidationError
    | JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet
    | None
):
    """Job Details

    Args:
        job_id (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet
    """

    return sync_detailed(
        job_id=job_id,
        client=client,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    job_id: int,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    HTTPValidationError
    | JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet
]:
    """Job Details

    Args:
        job_id (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    job_id: int,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> (
    HTTPValidationError
    | JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet
    | None
):
    """Job Details

    Args:
        job_id (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet
    """

    return (
        await asyncio_detailed(
            job_id=job_id,
            client=client,
            x_current_organization=x_current_organization,
        )
    ).parsed
