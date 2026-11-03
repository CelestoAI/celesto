from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.pool_bootstrap_request import PoolBootstrapRequest
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    host_id: str,
    computer_id: str,
    *,
    body: PoolBootstrapRequest,
    authorization: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/internal/pool/hosts/{host_id}/computers/{computer_id}/bootstrap".format(
            host_id=quote(str(host_id), safe=""),
            computer_id=quote(str(computer_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = response.json()
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
) -> Response[Any | HTTPValidationError]:
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
    body: PoolBootstrapRequest,
    authorization: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Bootstrap

    Args:
        host_id (str):
        computer_id (str):
        authorization (None | str | Unset):
        body (PoolBootstrapRequest): A host asks for a booted CI computer's runner start command,
            or reports its result (plan A).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        computer_id=computer_id,
        body=body,
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
    body: PoolBootstrapRequest,
    authorization: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Bootstrap

    Args:
        host_id (str):
        computer_id (str):
        authorization (None | str | Unset):
        body (PoolBootstrapRequest): A host asks for a booted CI computer's runner start command,
            or reports its result (plan A).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        host_id=host_id,
        computer_id=computer_id,
        client=client,
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    host_id: str,
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PoolBootstrapRequest,
    authorization: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Bootstrap

    Args:
        host_id (str):
        computer_id (str):
        authorization (None | str | Unset):
        body (PoolBootstrapRequest): A host asks for a booted CI computer's runner start command,
            or reports its result (plan A).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        computer_id=computer_id,
        body=body,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    host_id: str,
    computer_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PoolBootstrapRequest,
    authorization: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Bootstrap

    Args:
        host_id (str):
        computer_id (str):
        authorization (None | str | Unset):
        body (PoolBootstrapRequest): A host asks for a booted CI computer's runner start command,
            or reports its result (plan A).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            host_id=host_id,
            computer_id=computer_id,
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
