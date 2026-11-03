from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.job_step_log_v1_integrations_github_actions_jobs_job_id_steps_number_log_get_response_job_step_log_v1_integrations_github_actions_jobs_job_id_steps_number_log_get import (
    JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet,
)
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    job_id: int,
    number: int,
    *,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/integrations/github/actions/jobs/{job_id}/steps/{number}/log".format(
            job_id=quote(str(job_id), safe=""),
            number=quote(str(number), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet
    | None
):
    if response.status_code == 200:
        response_200 = JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet.from_dict(
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
    | JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    job_id: int,
    number: int,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    HTTPValidationError
    | JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet
]:
    """Job Step Log

     The log lines GitHub wrote while this step ran: the last 5,000, with `truncated` when more exist.

    Args:
        job_id (int):
        number (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        number=number,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    job_id: int,
    number: int,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> (
    HTTPValidationError
    | JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet
    | None
):
    """Job Step Log

     The log lines GitHub wrote while this step ran: the last 5,000, with `truncated` when more exist.

    Args:
        job_id (int):
        number (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet
    """

    return sync_detailed(
        job_id=job_id,
        number=number,
        client=client,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    job_id: int,
    number: int,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    HTTPValidationError
    | JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet
]:
    """Job Step Log

     The log lines GitHub wrote while this step ran: the last 5,000, with `truncated` when more exist.

    Args:
        job_id (int):
        number (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        number=number,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    job_id: int,
    number: int,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> (
    HTTPValidationError
    | JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet
    | None
):
    """Job Step Log

     The log lines GitHub wrote while this step ran: the last 5,000, with `truncated` when more exist.

    Args:
        job_id (int):
        number (int):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet
    """

    return (
        await asyncio_detailed(
            job_id=job_id,
            number=number,
            client=client,
            x_current_organization=x_current_organization,
        )
    ).parsed
