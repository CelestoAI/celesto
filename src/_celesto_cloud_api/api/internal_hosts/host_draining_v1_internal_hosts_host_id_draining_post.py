from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from typing import cast


def _get_kwargs(
    host_id: str,
    *,
    x_agent_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-agent-key"] = x_agent_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/internal/hosts/{host_id}/draining".format(
            host_id=quote(str(host_id), safe=""),
        ),
    }

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
    *,
    client: AuthenticatedClient | Client,
    x_agent_key: str,
) -> Response[Any | HTTPValidationError]:
    """Host agent reports imminent shutdown (spot termination or SIGTERM)

     Mark host as offline and trigger immediate cleanup of its computers.

    Sets OFFLINE directly (not DRAINING) because spot termination gives ~2 min
    and cleanup_offline_hosts keys off OFFLINE status. No time for graceful drain.

    Args:
        host_id (str):
        x_agent_key (str): Host agent shared secret

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        x_agent_key=x_agent_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_agent_key: str,
) -> Any | HTTPValidationError | None:
    """Host agent reports imminent shutdown (spot termination or SIGTERM)

     Mark host as offline and trigger immediate cleanup of its computers.

    Sets OFFLINE directly (not DRAINING) because spot termination gives ~2 min
    and cleanup_offline_hosts keys off OFFLINE status. No time for graceful drain.

    Args:
        host_id (str):
        x_agent_key (str): Host agent shared secret

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        host_id=host_id,
        client=client,
        x_agent_key=x_agent_key,
    ).parsed


async def asyncio_detailed(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_agent_key: str,
) -> Response[Any | HTTPValidationError]:
    """Host agent reports imminent shutdown (spot termination or SIGTERM)

     Mark host as offline and trigger immediate cleanup of its computers.

    Sets OFFLINE directly (not DRAINING) because spot termination gives ~2 min
    and cleanup_offline_hosts keys off OFFLINE status. No time for graceful drain.

    Args:
        host_id (str):
        x_agent_key (str): Host agent shared secret

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        x_agent_key=x_agent_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    host_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_agent_key: str,
) -> Any | HTTPValidationError | None:
    """Host agent reports imminent shutdown (spot termination or SIGTERM)

     Mark host as offline and trigger immediate cleanup of its computers.

    Sets OFFLINE directly (not DRAINING) because spot termination gives ~2 min
    and cleanup_offline_hosts keys off OFFLINE status. No time for graceful drain.

    Args:
        host_id (str):
        x_agent_key (str): Host agent shared secret

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            host_id=host_id,
            client=client,
            x_agent_key=x_agent_key,
        )
    ).parsed
