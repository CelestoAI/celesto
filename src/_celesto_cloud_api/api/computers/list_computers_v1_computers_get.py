from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.computer_list_response import ComputerListResponse
from ...models.computer_status import ComputerStatus
from ...models.computer_validation_error_response import ComputerValidationErrorResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    status: ComputerStatus | None | Unset = UNSET,
    template_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    params: dict[str, Any] = {}

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, ComputerStatus):
        json_status = status.value
    else:
        json_status = status
    params["status"] = json_status

    json_template_id: None | str | Unset
    if isinstance(template_id, Unset):
        json_template_id = UNSET
    else:
        json_template_id = template_id
    params["template_id"] = json_template_id

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/computers",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ComputerListResponse | ComputerValidationErrorResponse | None:
    if response.status_code == 200:
        response_200 = ComputerListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = ComputerValidationErrorResponse.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ComputerListResponse | ComputerValidationErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    status: ComputerStatus | None | Unset = UNSET,
    template_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    x_current_organization: str | Unset = UNSET,
) -> Response[ComputerListResponse | ComputerValidationErrorResponse]:
    """List compute VMs for the current organization

    Args:
        status (ComputerStatus | None | Unset):
        template_id (None | str | Unset):
        project_id (None | str | Unset):
        limit (int | Unset):  Default: 50.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ComputerListResponse | ComputerValidationErrorResponse]
    """

    kwargs = _get_kwargs(
        status=status,
        template_id=template_id,
        project_id=project_id,
        limit=limit,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    status: ComputerStatus | None | Unset = UNSET,
    template_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    x_current_organization: str | Unset = UNSET,
) -> ComputerListResponse | ComputerValidationErrorResponse | None:
    """List compute VMs for the current organization

    Args:
        status (ComputerStatus | None | Unset):
        template_id (None | str | Unset):
        project_id (None | str | Unset):
        limit (int | Unset):  Default: 50.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ComputerListResponse | ComputerValidationErrorResponse
    """

    return sync_detailed(
        client=client,
        status=status,
        template_id=template_id,
        project_id=project_id,
        limit=limit,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    status: ComputerStatus | None | Unset = UNSET,
    template_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    x_current_organization: str | Unset = UNSET,
) -> Response[ComputerListResponse | ComputerValidationErrorResponse]:
    """List compute VMs for the current organization

    Args:
        status (ComputerStatus | None | Unset):
        template_id (None | str | Unset):
        project_id (None | str | Unset):
        limit (int | Unset):  Default: 50.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ComputerListResponse | ComputerValidationErrorResponse]
    """

    kwargs = _get_kwargs(
        status=status,
        template_id=template_id,
        project_id=project_id,
        limit=limit,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    status: ComputerStatus | None | Unset = UNSET,
    template_id: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    x_current_organization: str | Unset = UNSET,
) -> ComputerListResponse | ComputerValidationErrorResponse | None:
    """List compute VMs for the current organization

    Args:
        status (ComputerStatus | None | Unset):
        template_id (None | str | Unset):
        project_id (None | str | Unset):
        limit (int | Unset):  Default: 50.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ComputerListResponse | ComputerValidationErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            status=status,
            template_id=template_id,
            project_id=project_id,
            limit=limit,
            x_current_organization=x_current_organization,
        )
    ).parsed
