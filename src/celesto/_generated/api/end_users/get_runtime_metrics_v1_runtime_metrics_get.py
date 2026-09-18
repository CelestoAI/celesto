from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.runtime_metrics_response import RuntimeMetricsResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    days: int | Unset = 30,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    params: dict[str, Any] = {}

    params["days"] = days

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/runtime/metrics",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | RuntimeMetricsResponse | None:
    if response.status_code == 200:
        response_200 = RuntimeMetricsResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | RuntimeMetricsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    days: int | Unset = 30,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | RuntimeMetricsResponse]:
    """Org runtime aggregates

     Runs and spend over time plus headline totals — the dashboard's data.

    The by-day series are sparse (days without activity are absent); clients
    zero-fill. ``success_rate`` is None until a run has settled, so a fresh
    org shows "—" instead of a fake 100%.

    Args:
        days (int | Unset):  Default: 30.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RuntimeMetricsResponse]
    """

    kwargs = _get_kwargs(
        days=days,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    days: int | Unset = 30,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | RuntimeMetricsResponse | None:
    """Org runtime aggregates

     Runs and spend over time plus headline totals — the dashboard's data.

    The by-day series are sparse (days without activity are absent); clients
    zero-fill. ``success_rate`` is None until a run has settled, so a fresh
    org shows "—" instead of a fake 100%.

    Args:
        days (int | Unset):  Default: 30.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RuntimeMetricsResponse
    """

    return sync_detailed(
        client=client,
        days=days,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    days: int | Unset = 30,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | RuntimeMetricsResponse]:
    """Org runtime aggregates

     Runs and spend over time plus headline totals — the dashboard's data.

    The by-day series are sparse (days without activity are absent); clients
    zero-fill. ``success_rate`` is None until a run has settled, so a fresh
    org shows "—" instead of a fake 100%.

    Args:
        days (int | Unset):  Default: 30.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RuntimeMetricsResponse]
    """

    kwargs = _get_kwargs(
        days=days,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    days: int | Unset = 30,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | RuntimeMetricsResponse | None:
    """Org runtime aggregates

     Runs and spend over time plus headline totals — the dashboard's data.

    The by-day series are sparse (days without activity are absent); clients
    zero-fill. ``success_rate`` is None until a run has settled, so a fresh
    org shows "—" instead of a fake 100%.

    Args:
        days (int | Unset):  Default: 30.
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RuntimeMetricsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            days=days,
            x_current_organization=x_current_organization,
        )
    ).parsed
