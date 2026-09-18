from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.computer_create_request import ComputerCreateRequest
from ...models.computer_response import ComputerResponse
from ...models.computer_validation_error_response import ComputerValidationErrorResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    body: ComputerCreateRequest,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/computers",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ComputerResponse | ComputerValidationErrorResponse | None:
    if response.status_code == 201:
        response_201 = ComputerResponse.from_dict(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = ComputerValidationErrorResponse.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ComputerResponse | ComputerValidationErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ComputerCreateRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[ComputerResponse | ComputerValidationErrorResponse]:
    """Create a new compute VM

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (ComputerCreateRequest): Request to create a new compute VM.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ComputerResponse | ComputerValidationErrorResponse]
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
    body: ComputerCreateRequest,
    x_current_organization: str | Unset = UNSET,
) -> ComputerResponse | ComputerValidationErrorResponse | None:
    """Create a new compute VM

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (ComputerCreateRequest): Request to create a new compute VM.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ComputerResponse | ComputerValidationErrorResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ComputerCreateRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[ComputerResponse | ComputerValidationErrorResponse]:
    """Create a new compute VM

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (ComputerCreateRequest): Request to create a new compute VM.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ComputerResponse | ComputerValidationErrorResponse]
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
    body: ComputerCreateRequest,
    x_current_organization: str | Unset = UNSET,
) -> ComputerResponse | ComputerValidationErrorResponse | None:
    """Create a new compute VM

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (ComputerCreateRequest): Request to create a new compute VM.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ComputerResponse | ComputerValidationErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_current_organization=x_current_organization,
        )
    ).parsed
