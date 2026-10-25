from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.get_sandbox_sizes_v1_billing_sizes_get_price_version import (
    GetSandboxSizesV1BillingSizesGetPriceVersion,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.sandbox_size_response import SandboxSizeResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    price_version: GetSandboxSizesV1BillingSizesGetPriceVersion
    | Unset = GetSandboxSizesV1BillingSizesGetPriceVersion.USAGE_V2,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_price_version: str | Unset = UNSET
    if not isinstance(price_version, Unset):
        json_price_version = price_version.value

    params["price_version"] = json_price_version

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/billing/sizes",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[SandboxSizeResponse] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = SandboxSizeResponse.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[SandboxSizeResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    price_version: GetSandboxSizesV1BillingSizesGetPriceVersion
    | Unset = GetSandboxSizesV1BillingSizesGetPriceVersion.USAGE_V2,
) -> Response[HTTPValidationError | list[SandboxSizeResponse]]:
    """Get usage-priced sandbox sizes

     Show prices only when the Autumn catalog matches this release.

    Args:
        price_version (GetSandboxSizesV1BillingSizesGetPriceVersion | Unset):  Default:
            GetSandboxSizesV1BillingSizesGetPriceVersion.USAGE_V2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[SandboxSizeResponse]]
    """

    kwargs = _get_kwargs(
        price_version=price_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    price_version: GetSandboxSizesV1BillingSizesGetPriceVersion
    | Unset = GetSandboxSizesV1BillingSizesGetPriceVersion.USAGE_V2,
) -> HTTPValidationError | list[SandboxSizeResponse] | None:
    """Get usage-priced sandbox sizes

     Show prices only when the Autumn catalog matches this release.

    Args:
        price_version (GetSandboxSizesV1BillingSizesGetPriceVersion | Unset):  Default:
            GetSandboxSizesV1BillingSizesGetPriceVersion.USAGE_V2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[SandboxSizeResponse]
    """

    return sync_detailed(
        client=client,
        price_version=price_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    price_version: GetSandboxSizesV1BillingSizesGetPriceVersion
    | Unset = GetSandboxSizesV1BillingSizesGetPriceVersion.USAGE_V2,
) -> Response[HTTPValidationError | list[SandboxSizeResponse]]:
    """Get usage-priced sandbox sizes

     Show prices only when the Autumn catalog matches this release.

    Args:
        price_version (GetSandboxSizesV1BillingSizesGetPriceVersion | Unset):  Default:
            GetSandboxSizesV1BillingSizesGetPriceVersion.USAGE_V2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[SandboxSizeResponse]]
    """

    kwargs = _get_kwargs(
        price_version=price_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    price_version: GetSandboxSizesV1BillingSizesGetPriceVersion
    | Unset = GetSandboxSizesV1BillingSizesGetPriceVersion.USAGE_V2,
) -> HTTPValidationError | list[SandboxSizeResponse] | None:
    """Get usage-priced sandbox sizes

     Show prices only when the Autumn catalog matches this release.

    Args:
        price_version (GetSandboxSizesV1BillingSizesGetPriceVersion | Unset):  Default:
            GetSandboxSizesV1BillingSizesGetPriceVersion.USAGE_V2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[SandboxSizeResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            price_version=price_version,
        )
    ).parsed
