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
    org_id: str,
    user_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/v1/organizations/{org_id}/members/{user_id}".format(
            org_id=quote(str(org_id), safe=""),
            user_id=quote(str(user_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

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
    org_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | HTTPValidationError]:
    """Remove a member from the organization

     Soft-deletes a member (sets status=REMOVED). Requires admin permissions.

    Args:
        org_id (str): The ID of the organization
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        user_id=user_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    org_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | HTTPValidationError | None:
    """Remove a member from the organization

     Soft-deletes a member (sets status=REMOVED). Requires admin permissions.

    Args:
        org_id (str): The ID of the organization
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        org_id=org_id,
        user_id=user_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | HTTPValidationError]:
    """Remove a member from the organization

     Soft-deletes a member (sets status=REMOVED). Requires admin permissions.

    Args:
        org_id (str): The ID of the organization
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        user_id=user_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | HTTPValidationError | None:
    """Remove a member from the organization

     Soft-deletes a member (sets status=REMOVED). Requires admin permissions.

    Args:
        org_id (str): The ID of the organization
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            user_id=user_id,
            client=client,
        )
    ).parsed
