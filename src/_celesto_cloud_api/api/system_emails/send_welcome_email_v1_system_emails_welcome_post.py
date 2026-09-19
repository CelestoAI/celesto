from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.email_response import EmailResponse
from ...models.http_validation_error import HTTPValidationError
from ...models.welcome_email_request import WelcomeEmailRequest
from typing import cast


def _get_kwargs(
    *,
    body: WelcomeEmailRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/system-emails/welcome",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EmailResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = EmailResponse.from_dict(response.json())

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
) -> Response[EmailResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: WelcomeEmailRequest,
) -> Response[EmailResponse | HTTPValidationError]:
    """Send system welcome email

     Send a welcome email to a new user using the system's Resend service.

        **System Email Service**: Sends platform-generated emails via Resend.
        This is NOT for user-initiated emails - those use the user-emails endpoints with Gmail API.

        Used for onboarding new users to the platform. Requires authentication.

    Args:
        body (WelcomeEmailRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmailResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: WelcomeEmailRequest,
) -> EmailResponse | HTTPValidationError | None:
    """Send system welcome email

     Send a welcome email to a new user using the system's Resend service.

        **System Email Service**: Sends platform-generated emails via Resend.
        This is NOT for user-initiated emails - those use the user-emails endpoints with Gmail API.

        Used for onboarding new users to the platform. Requires authentication.

    Args:
        body (WelcomeEmailRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmailResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: WelcomeEmailRequest,
) -> Response[EmailResponse | HTTPValidationError]:
    """Send system welcome email

     Send a welcome email to a new user using the system's Resend service.

        **System Email Service**: Sends platform-generated emails via Resend.
        This is NOT for user-initiated emails - those use the user-emails endpoints with Gmail API.

        Used for onboarding new users to the platform. Requires authentication.

    Args:
        body (WelcomeEmailRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmailResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: WelcomeEmailRequest,
) -> EmailResponse | HTTPValidationError | None:
    """Send system welcome email

     Send a welcome email to a new user using the system's Resend service.

        **System Email Service**: Sends platform-generated emails via Resend.
        This is NOT for user-initiated emails - those use the user-emails endpoints with Gmail API.

        Used for onboarding new users to the platform. Requires authentication.

    Args:
        body (WelcomeEmailRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmailResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
