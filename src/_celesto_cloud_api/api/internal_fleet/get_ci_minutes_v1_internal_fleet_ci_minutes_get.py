from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.ci_minutes_series import CiMinutesSeries
from ...models.get_ci_minutes_v1_internal_fleet_ci_minutes_get_interval import (
    GetCiMinutesV1InternalFleetCiMinutesGetInterval,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    interval: GetCiMinutesV1InternalFleetCiMinutesGetInterval
    | Unset = GetCiMinutesV1InternalFleetCiMinutesGetInterval.DAY,
    days: int | Unset = 30,
    exclude_internal: bool | Unset = True,
    authorization: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    params: dict[str, Any] = {}

    json_interval: str | Unset = UNSET
    if not isinstance(interval, Unset):
        json_interval = interval.value

    params["interval"] = json_interval

    params["days"] = days

    params["exclude_internal"] = exclude_internal

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/internal/fleet/ci-minutes",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CiMinutesSeries | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CiMinutesSeries.from_dict(response.json())

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
) -> Response[CiMinutesSeries | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    interval: GetCiMinutesV1InternalFleetCiMinutesGetInterval
    | Unset = GetCiMinutesV1InternalFleetCiMinutesGetInterval.DAY,
    days: int | Unset = 30,
    exclude_internal: bool | Unset = True,
    authorization: None | str | Unset = UNSET,
) -> Response[CiMinutesSeries | HTTPValidationError]:
    """Get Ci Minutes

    Args:
        interval (GetCiMinutesV1InternalFleetCiMinutesGetInterval | Unset):  Default:
            GetCiMinutesV1InternalFleetCiMinutesGetInterval.DAY.
        days (int | Unset):  Default: 30.
        exclude_internal (bool | Unset):  Default: True.
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CiMinutesSeries | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        interval=interval,
        days=days,
        exclude_internal=exclude_internal,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    interval: GetCiMinutesV1InternalFleetCiMinutesGetInterval
    | Unset = GetCiMinutesV1InternalFleetCiMinutesGetInterval.DAY,
    days: int | Unset = 30,
    exclude_internal: bool | Unset = True,
    authorization: None | str | Unset = UNSET,
) -> CiMinutesSeries | HTTPValidationError | None:
    """Get Ci Minutes

    Args:
        interval (GetCiMinutesV1InternalFleetCiMinutesGetInterval | Unset):  Default:
            GetCiMinutesV1InternalFleetCiMinutesGetInterval.DAY.
        days (int | Unset):  Default: 30.
        exclude_internal (bool | Unset):  Default: True.
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CiMinutesSeries | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        interval=interval,
        days=days,
        exclude_internal=exclude_internal,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    interval: GetCiMinutesV1InternalFleetCiMinutesGetInterval
    | Unset = GetCiMinutesV1InternalFleetCiMinutesGetInterval.DAY,
    days: int | Unset = 30,
    exclude_internal: bool | Unset = True,
    authorization: None | str | Unset = UNSET,
) -> Response[CiMinutesSeries | HTTPValidationError]:
    """Get Ci Minutes

    Args:
        interval (GetCiMinutesV1InternalFleetCiMinutesGetInterval | Unset):  Default:
            GetCiMinutesV1InternalFleetCiMinutesGetInterval.DAY.
        days (int | Unset):  Default: 30.
        exclude_internal (bool | Unset):  Default: True.
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CiMinutesSeries | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        interval=interval,
        days=days,
        exclude_internal=exclude_internal,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    interval: GetCiMinutesV1InternalFleetCiMinutesGetInterval
    | Unset = GetCiMinutesV1InternalFleetCiMinutesGetInterval.DAY,
    days: int | Unset = 30,
    exclude_internal: bool | Unset = True,
    authorization: None | str | Unset = UNSET,
) -> CiMinutesSeries | HTTPValidationError | None:
    """Get Ci Minutes

    Args:
        interval (GetCiMinutesV1InternalFleetCiMinutesGetInterval | Unset):  Default:
            GetCiMinutesV1InternalFleetCiMinutesGetInterval.DAY.
        days (int | Unset):  Default: 30.
        exclude_internal (bool | Unset):  Default: True.
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CiMinutesSeries | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            interval=interval,
            days=days,
            exclude_internal=exclude_internal,
            authorization=authorization,
        )
    ).parsed
