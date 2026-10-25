from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.fleet_release_running_computer_state import (
    FleetReleaseRunningComputerState,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast
from uuid import UUID


def _get_kwargs(
    host_id: str,
    computer_id: str,
    *,
    state_id: UUID,
    authorization: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    params: dict[str, Any] = {}

    json_state_id = str(state_id)
    params["state_id"] = json_state_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/internal/fleet-releases/hosts/{host_id}/computers/{computer_id}".format(
            host_id=quote(str(host_id), safe=""),
            computer_id=quote(str(computer_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> FleetReleaseRunningComputerState | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = FleetReleaseRunningComputerState.from_dict(response.json())

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
) -> Response[FleetReleaseRunningComputerState | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    host_id: str,
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    state_id: UUID,
    authorization: None | str | Unset = UNSET,
) -> Response[FleetReleaseRunningComputerState | HTTPValidationError]:
    """Running Computer

     Read the runner's expected live sandbox binding without tenant exposure.

    Args:
        host_id (str):
        computer_id (str):
        state_id (UUID):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FleetReleaseRunningComputerState | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        computer_id=computer_id,
        state_id=state_id,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    host_id: str,
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    state_id: UUID,
    authorization: None | str | Unset = UNSET,
) -> FleetReleaseRunningComputerState | HTTPValidationError | None:
    """Running Computer

     Read the runner's expected live sandbox binding without tenant exposure.

    Args:
        host_id (str):
        computer_id (str):
        state_id (UUID):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FleetReleaseRunningComputerState | HTTPValidationError
    """

    return sync_detailed(
        host_id=host_id,
        computer_id=computer_id,
        client=client,
        state_id=state_id,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    host_id: str,
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    state_id: UUID,
    authorization: None | str | Unset = UNSET,
) -> Response[FleetReleaseRunningComputerState | HTTPValidationError]:
    """Running Computer

     Read the runner's expected live sandbox binding without tenant exposure.

    Args:
        host_id (str):
        computer_id (str):
        state_id (UUID):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FleetReleaseRunningComputerState | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        computer_id=computer_id,
        state_id=state_id,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    host_id: str,
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    state_id: UUID,
    authorization: None | str | Unset = UNSET,
) -> FleetReleaseRunningComputerState | HTTPValidationError | None:
    """Running Computer

     Read the runner's expected live sandbox binding without tenant exposure.

    Args:
        host_id (str):
        computer_id (str):
        state_id (UUID):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FleetReleaseRunningComputerState | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            host_id=host_id,
            computer_id=computer_id,
            client=client,
            state_id=state_id,
            authorization=authorization,
        )
    ).parsed
