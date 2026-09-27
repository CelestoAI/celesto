from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.acknowledge_drain_v1_internal_ingress_routes_route_id_drained_post_response_acknowledge_drain_v1_internal_ingress_routes_route_id_drained_post import (
    AcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPostResponseAcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPost,
)
from ...models.drain_acknowledgement import DrainAcknowledgement
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    route_id: str,
    *,
    body: DrainAcknowledgement,
    authorization: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/internal/ingress/routes/{route_id}/drained".format(
            route_id=quote(str(route_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    AcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPostResponseAcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPost
    | HTTPValidationError
    | None
):
    if response.status_code == 200:
        response_200 = AcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPostResponseAcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPost.from_dict(
            response.json()
        )

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
) -> Response[
    AcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPostResponseAcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPost
    | HTTPValidationError
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    route_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DrainAcknowledgement,
    authorization: None | str | Unset = UNSET,
) -> Response[
    AcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPostResponseAcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPost
    | HTTPValidationError
]:
    """Acknowledge Drain

    Args:
        route_id (str):
        authorization (None | str | Unset):
        body (DrainAcknowledgement):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPostResponseAcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        route_id=route_id,
        body=body,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    route_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DrainAcknowledgement,
    authorization: None | str | Unset = UNSET,
) -> (
    AcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPostResponseAcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPost
    | HTTPValidationError
    | None
):
    """Acknowledge Drain

    Args:
        route_id (str):
        authorization (None | str | Unset):
        body (DrainAcknowledgement):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPostResponseAcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPost | HTTPValidationError
    """

    return sync_detailed(
        route_id=route_id,
        client=client,
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    route_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DrainAcknowledgement,
    authorization: None | str | Unset = UNSET,
) -> Response[
    AcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPostResponseAcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPost
    | HTTPValidationError
]:
    """Acknowledge Drain

    Args:
        route_id (str):
        authorization (None | str | Unset):
        body (DrainAcknowledgement):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPostResponseAcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        route_id=route_id,
        body=body,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    route_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DrainAcknowledgement,
    authorization: None | str | Unset = UNSET,
) -> (
    AcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPostResponseAcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPost
    | HTTPValidationError
    | None
):
    """Acknowledge Drain

    Args:
        route_id (str):
        authorization (None | str | Unset):
        body (DrainAcknowledgement):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPostResponseAcknowledgeDrainV1InternalIngressRoutesRouteIdDrainedPost | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            route_id=route_id,
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
