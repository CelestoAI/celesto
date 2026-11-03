from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.usage_spend_response import UsageSpendResponse
from ...types import UNSET, Unset
from typing import cast
import datetime


def _get_kwargs(
    *,
    from_: datetime.date | None | Unset = UNSET,
    to: datetime.date | None | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    params: dict[str, Any] = {}

    json_from_: None | str | Unset
    if isinstance(from_, Unset):
        json_from_ = UNSET
    elif isinstance(from_, datetime.date):
        json_from_ = from_.isoformat()
    else:
        json_from_ = from_
    params["from"] = json_from_

    json_to: None | str | Unset
    if isinstance(to, Unset):
        json_to = UNSET
    elif isinstance(to, datetime.date):
        json_to = to.isoformat()
    else:
        json_to = to
    params["to"] = json_to

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/billing/usage/spend",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | UsageSpendResponse | None:
    if response.status_code == 200:
        response_200 = UsageSpendResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | UsageSpendResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    from_: datetime.date | None | Unset = UNSET,
    to: datetime.date | None | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | UsageSpendResponse]:
    """Get where sandbox credit was spent

    Args:
        from_ (datetime.date | None | Unset): First UTC day; defaults to the first of the `to`
            month
        to (datetime.date | None | Unset): Last UTC day, inclusive; defaults to today, capped at
            the range limit
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | UsageSpendResponse]
    """

    kwargs = _get_kwargs(
        from_=from_,
        to=to,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    from_: datetime.date | None | Unset = UNSET,
    to: datetime.date | None | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | UsageSpendResponse | None:
    """Get where sandbox credit was spent

    Args:
        from_ (datetime.date | None | Unset): First UTC day; defaults to the first of the `to`
            month
        to (datetime.date | None | Unset): Last UTC day, inclusive; defaults to today, capped at
            the range limit
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | UsageSpendResponse
    """

    return sync_detailed(
        client=client,
        from_=from_,
        to=to,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    from_: datetime.date | None | Unset = UNSET,
    to: datetime.date | None | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | UsageSpendResponse]:
    """Get where sandbox credit was spent

    Args:
        from_ (datetime.date | None | Unset): First UTC day; defaults to the first of the `to`
            month
        to (datetime.date | None | Unset): Last UTC day, inclusive; defaults to today, capped at
            the range limit
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | UsageSpendResponse]
    """

    kwargs = _get_kwargs(
        from_=from_,
        to=to,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    from_: datetime.date | None | Unset = UNSET,
    to: datetime.date | None | Unset = UNSET,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | UsageSpendResponse | None:
    """Get where sandbox credit was spent

    Args:
        from_ (datetime.date | None | Unset): First UTC day; defaults to the first of the `to`
            month
        to (datetime.date | None | Unset): Last UTC day, inclusive; defaults to today, capped at
            the range limit
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | UsageSpendResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            from_=from_,
            to=to,
            x_current_organization=x_current_organization,
        )
    ).parsed
