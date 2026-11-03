from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.job_steps_v1_integrations_github_actions_jobs_job_id_steps_get_response_job_steps_v1_integrations_github_actions_jobs_job_id_steps_get import (
    JobStepsV1IntegrationsGithubActionsJobsJobIdStepsGetResponseJobStepsV1IntegrationsGithubActionsJobsJobIdStepsGet,
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
        "url": "/v1/integrations/github/actions/jobs/{job_id}/steps".format(
            job_id=quote(str(job_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | JobStepsV1IntegrationsGithubActionsJobsJobIdStepsGetResponseJobStepsV1IntegrationsGithubActionsJobsJobIdStepsGet
    | None
):
    if response.status_code == 200:
        response_200 = JobStepsV1IntegrationsGithubActionsJobsJobIdStepsGetResponseJobStepsV1IntegrationsGithubActionsJobsJobIdStepsGet.from_dict(
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
    | JobStepsV1IntegrationsGithubActionsJobsJobIdStepsGetResponseJobStepsV1IntegrationsGithubActionsJobsJobIdStepsGet
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
    | JobStepsV1IntegrationsGithubActionsJobsJobIdStepsGetResponseJobStepsV1IntegrationsGithubActionsJobsJobIdStepsGet
]:
    """Job Steps

     GitHub's steps for this job, read from GitHub (cached for a few seconds).

    Args:
        job_id (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | JobStepsV1IntegrationsGithubActionsJobsJobIdStepsGetResponseJobStepsV1IntegrationsGithubActionsJobsJobIdStepsGet]
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
    | JobStepsV1IntegrationsGithubActionsJobsJobIdStepsGetResponseJobStepsV1IntegrationsGithubActionsJobsJobIdStepsGet
    | None
):
    """Job Steps

     GitHub's steps for this job, read from GitHub (cached for a few seconds).

    Args:
        job_id (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | JobStepsV1IntegrationsGithubActionsJobsJobIdStepsGetResponseJobStepsV1IntegrationsGithubActionsJobsJobIdStepsGet
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
    | JobStepsV1IntegrationsGithubActionsJobsJobIdStepsGetResponseJobStepsV1IntegrationsGithubActionsJobsJobIdStepsGet
]:
    """Job Steps

     GitHub's steps for this job, read from GitHub (cached for a few seconds).

    Args:
        job_id (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | JobStepsV1IntegrationsGithubActionsJobsJobIdStepsGetResponseJobStepsV1IntegrationsGithubActionsJobsJobIdStepsGet]
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
    | JobStepsV1IntegrationsGithubActionsJobsJobIdStepsGetResponseJobStepsV1IntegrationsGithubActionsJobsJobIdStepsGet
    | None
):
    """Job Steps

     GitHub's steps for this job, read from GitHub (cached for a few seconds).

    Args:
        job_id (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | JobStepsV1IntegrationsGithubActionsJobsJobIdStepsGetResponseJobStepsV1IntegrationsGithubActionsJobsJobIdStepsGet
    """

    return (
        await asyncio_detailed(
            job_id=job_id,
            client=client,
            x_current_organization=x_current_organization,
        )
    ).parsed
