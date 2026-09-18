from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.get_user_features_v1_features_get_response_get_user_features_v1_features_get import (
    GetUserFeaturesV1FeaturesGetResponseGetUserFeaturesV1FeaturesGet,
)
from typing import cast


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/features/",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetUserFeaturesV1FeaturesGetResponseGetUserFeaturesV1FeaturesGet | None:
    if response.status_code == 200:
        response_200 = (
            GetUserFeaturesV1FeaturesGetResponseGetUserFeaturesV1FeaturesGet.from_dict(
                response.json()
            )
        )

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetUserFeaturesV1FeaturesGetResponseGetUserFeaturesV1FeaturesGet]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetUserFeaturesV1FeaturesGetResponseGetUserFeaturesV1FeaturesGet]:
    """Get User Features

     Get current user's feature access map

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetUserFeaturesV1FeaturesGetResponseGetUserFeaturesV1FeaturesGet]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> GetUserFeaturesV1FeaturesGetResponseGetUserFeaturesV1FeaturesGet | None:
    """Get User Features

     Get current user's feature access map

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetUserFeaturesV1FeaturesGetResponseGetUserFeaturesV1FeaturesGet
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetUserFeaturesV1FeaturesGetResponseGetUserFeaturesV1FeaturesGet]:
    """Get User Features

     Get current user's feature access map

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetUserFeaturesV1FeaturesGetResponseGetUserFeaturesV1FeaturesGet]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> GetUserFeaturesV1FeaturesGetResponseGetUserFeaturesV1FeaturesGet | None:
    """Get User Features

     Get current user's feature access map

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetUserFeaturesV1FeaturesGetResponseGetUserFeaturesV1FeaturesGet
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
