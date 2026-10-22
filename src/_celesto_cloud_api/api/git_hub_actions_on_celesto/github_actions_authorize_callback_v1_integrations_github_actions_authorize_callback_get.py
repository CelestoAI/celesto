from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    state: None | str | Unset = UNSET,
    code: None | str | Unset = UNSET,
    error: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_state: None | str | Unset
    if isinstance(state, Unset):
        json_state = UNSET
    else:
        json_state = state
    params["state"] = json_state

    json_code: None | str | Unset
    if isinstance(code, Unset):
        json_code = UNSET
    else:
        json_code = code
    params["code"] = json_code

    json_error: None | str | Unset
    if isinstance(error, Unset):
        json_error = UNSET
    else:
        json_error = error
    params["error"] = json_error

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/integrations/github/actions/authorize-callback",
        "params": params,
    }

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
    *,
    client: AuthenticatedClient | Client,
    state: None | str | Unset = UNSET,
    code: None | str | Unset = UNSET,
    error: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Github Actions Authorize Callback

     GitHub's redirect after the user approves the App; forwards to the setup page.

    This request carries no Celesto session, so it does no work and consumes
    nothing (D-10). The signed-in page posts `state` and `code` to
    `authorize-complete`, which checks the user who started the flow is the one
    finishing it. The state is read only to keep the installation on the page.

    Args:
        state (None | str | Unset):
        code (None | str | Unset):
        error (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        state=state,
        code=code,
        error=error,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    state: None | str | Unset = UNSET,
    code: None | str | Unset = UNSET,
    error: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Github Actions Authorize Callback

     GitHub's redirect after the user approves the App; forwards to the setup page.

    This request carries no Celesto session, so it does no work and consumes
    nothing (D-10). The signed-in page posts `state` and `code` to
    `authorize-complete`, which checks the user who started the flow is the one
    finishing it. The state is read only to keep the installation on the page.

    Args:
        state (None | str | Unset):
        code (None | str | Unset):
        error (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        state=state,
        code=code,
        error=error,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    state: None | str | Unset = UNSET,
    code: None | str | Unset = UNSET,
    error: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Github Actions Authorize Callback

     GitHub's redirect after the user approves the App; forwards to the setup page.

    This request carries no Celesto session, so it does no work and consumes
    nothing (D-10). The signed-in page posts `state` and `code` to
    `authorize-complete`, which checks the user who started the flow is the one
    finishing it. The state is read only to keep the installation on the page.

    Args:
        state (None | str | Unset):
        code (None | str | Unset):
        error (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        state=state,
        code=code,
        error=error,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    state: None | str | Unset = UNSET,
    code: None | str | Unset = UNSET,
    error: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Github Actions Authorize Callback

     GitHub's redirect after the user approves the App; forwards to the setup page.

    This request carries no Celesto session, so it does no work and consumes
    nothing (D-10). The signed-in page posts `state` and `code` to
    `authorize-complete`, which checks the user who started the flow is the one
    finishing it. The state is read only to keep the installation on the page.

    Args:
        state (None | str | Unset):
        code (None | str | Unset):
        error (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            state=state,
            code=code,
            error=error,
        )
    ).parsed
