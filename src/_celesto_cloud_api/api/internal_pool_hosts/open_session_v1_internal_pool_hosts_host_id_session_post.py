from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.open_session_v1_internal_pool_hosts_host_id_session_post_response_open_session_v1_internal_pool_hosts_host_id_session_post import (
    OpenSessionV1InternalPoolHostsHostIdSessionPostResponseOpenSessionV1InternalPoolHostsHostIdSessionPost,
)
from ...models.session_request import SessionRequest
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    host_id: str,
    *,
    body: SessionRequest,
    authorization: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/internal/pool/hosts/{host_id}/session".format(
            host_id=quote(str(host_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | OpenSessionV1InternalPoolHostsHostIdSessionPostResponseOpenSessionV1InternalPoolHostsHostIdSessionPost
    | None
):
    if response.status_code == 200:
        response_200 = OpenSessionV1InternalPoolHostsHostIdSessionPostResponseOpenSessionV1InternalPoolHostsHostIdSessionPost.from_dict(
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
    HTTPValidationError
    | OpenSessionV1InternalPoolHostsHostIdSessionPostResponseOpenSessionV1InternalPoolHostsHostIdSessionPost
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SessionRequest,
    authorization: None | str | Unset = UNSET,
) -> Response[
    HTTPValidationError
    | OpenSessionV1InternalPoolHostsHostIdSessionPostResponseOpenSessionV1InternalPoolHostsHostIdSessionPost
]:
    """Open Session

    Args:
        host_id (str):
        authorization (None | str | Unset):
        body (SessionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OpenSessionV1InternalPoolHostsHostIdSessionPostResponseOpenSessionV1InternalPoolHostsHostIdSessionPost]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        body=body,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SessionRequest,
    authorization: None | str | Unset = UNSET,
) -> (
    HTTPValidationError
    | OpenSessionV1InternalPoolHostsHostIdSessionPostResponseOpenSessionV1InternalPoolHostsHostIdSessionPost
    | None
):
    """Open Session

    Args:
        host_id (str):
        authorization (None | str | Unset):
        body (SessionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OpenSessionV1InternalPoolHostsHostIdSessionPostResponseOpenSessionV1InternalPoolHostsHostIdSessionPost
    """

    return sync_detailed(
        host_id=host_id,
        client=client,
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SessionRequest,
    authorization: None | str | Unset = UNSET,
) -> Response[
    HTTPValidationError
    | OpenSessionV1InternalPoolHostsHostIdSessionPostResponseOpenSessionV1InternalPoolHostsHostIdSessionPost
]:
    """Open Session

    Args:
        host_id (str):
        authorization (None | str | Unset):
        body (SessionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OpenSessionV1InternalPoolHostsHostIdSessionPostResponseOpenSessionV1InternalPoolHostsHostIdSessionPost]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        body=body,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SessionRequest,
    authorization: None | str | Unset = UNSET,
) -> (
    HTTPValidationError
    | OpenSessionV1InternalPoolHostsHostIdSessionPostResponseOpenSessionV1InternalPoolHostsHostIdSessionPost
    | None
):
    """Open Session

    Args:
        host_id (str):
        authorization (None | str | Unset):
        body (SessionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OpenSessionV1InternalPoolHostsHostIdSessionPostResponseOpenSessionV1InternalPoolHostsHostIdSessionPost
    """

    return (
        await asyncio_detailed(
            host_id=host_id,
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
