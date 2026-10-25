from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.platform_analytics import PlatformAnalytics
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    exclude_internal: bool | Unset = True,
    authorization: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    params: dict[str, Any] = {}

    params["exclude_internal"] = exclude_internal

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/internal/fleet/platform-analytics",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | PlatformAnalytics | None:
    if response.status_code == 200:
        response_200 = PlatformAnalytics.from_dict(response.json())

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
) -> Response[HTTPValidationError | PlatformAnalytics]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    exclude_internal: bool | Unset = True,
    authorization: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | PlatformAnalytics]:
    """Get Platform Analytics

    Args:
        exclude_internal (bool | Unset):  Default: True.
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PlatformAnalytics]
    """

    kwargs = _get_kwargs(
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
    exclude_internal: bool | Unset = True,
    authorization: None | str | Unset = UNSET,
) -> HTTPValidationError | PlatformAnalytics | None:
    """Get Platform Analytics

    Args:
        exclude_internal (bool | Unset):  Default: True.
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PlatformAnalytics
    """

    return sync_detailed(
        client=client,
        exclude_internal=exclude_internal,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    exclude_internal: bool | Unset = True,
    authorization: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | PlatformAnalytics]:
    """Get Platform Analytics

    Args:
        exclude_internal (bool | Unset):  Default: True.
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PlatformAnalytics]
    """

    kwargs = _get_kwargs(
        exclude_internal=exclude_internal,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    exclude_internal: bool | Unset = True,
    authorization: None | str | Unset = UNSET,
) -> HTTPValidationError | PlatformAnalytics | None:
    """Get Platform Analytics

    Args:
        exclude_internal (bool | Unset):  Default: True.
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PlatformAnalytics
    """

    return (
        await asyncio_detailed(
            client=client,
            exclude_internal=exclude_internal,
            authorization=authorization,
        )
    ).parsed
