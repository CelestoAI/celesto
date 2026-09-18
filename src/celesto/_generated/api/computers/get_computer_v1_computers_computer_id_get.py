from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.computer_response import ComputerResponse
from ...models.computer_validation_error_response import ComputerValidationErrorResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    computer_id: str,
    *,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/computers/{computer_id}".format(
            computer_id=quote(str(computer_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ComputerResponse | ComputerValidationErrorResponse | None:
    if response.status_code == 200:
        response_200 = ComputerResponse.from_dict(response.json())

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
) -> Response[ComputerResponse | ComputerValidationErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> Response[ComputerResponse | ComputerValidationErrorResponse]:
    """Get compute VM status and connection info

    Args:
        computer_id (str):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ComputerResponse | ComputerValidationErrorResponse]
    """

    kwargs = _get_kwargs(
        computer_id=computer_id,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> ComputerResponse | ComputerValidationErrorResponse | None:
    """Get compute VM status and connection info

    Args:
        computer_id (str):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ComputerResponse | ComputerValidationErrorResponse
    """

    return sync_detailed(
        computer_id=computer_id,
        client=client,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> Response[ComputerResponse | ComputerValidationErrorResponse]:
    """Get compute VM status and connection info

    Args:
        computer_id (str):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ComputerResponse | ComputerValidationErrorResponse]
    """

    kwargs = _get_kwargs(
        computer_id=computer_id,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> ComputerResponse | ComputerValidationErrorResponse | None:
    """Get compute VM status and connection info

    Args:
        computer_id (str):
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ComputerResponse | ComputerValidationErrorResponse
    """

    return (
        await asyncio_detailed(
            computer_id=computer_id,
            client=client,
            x_current_organization=x_current_organization,
        )
    ).parsed
