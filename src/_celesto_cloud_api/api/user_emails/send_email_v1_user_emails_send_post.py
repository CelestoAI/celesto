from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.send_email_request import SendEmailRequest
from ...models.send_email_response import SendEmailResponse
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    body: SendEmailRequest,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/user-emails/send",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | SendEmailResponse | None:
    if response.status_code == 200:
        response_200 = SendEmailResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | SendEmailResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SendEmailRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | SendEmailResponse]:
    """Send email via user's Gmail account

     Send an email on behalf of the authenticated user using their connected Gmail account.

        **User Email Service**: Sends emails through the user's personal Gmail via Google Gmail API.
        This is NOT for system emails - those use the separate system-emails endpoints with Resend.

        Requires the user to have an active Google/Gmail integration configured.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (SendEmailRequest): Request schema for sending an email Example: {'bcc':
            ['bcc@example.com'], 'body': 'Thank you for the meeting today...', 'cc':
            ['cc@example.com'], 'html_body': '<p>Thank you for the meeting today...</p>', 'reply_to':
            'sender@example.com', 'subject': 'Meeting Follow-up', 'to_email':
            'recipient@example.com'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SendEmailResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: SendEmailRequest,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | SendEmailResponse | None:
    """Send email via user's Gmail account

     Send an email on behalf of the authenticated user using their connected Gmail account.

        **User Email Service**: Sends emails through the user's personal Gmail via Google Gmail API.
        This is NOT for system emails - those use the separate system-emails endpoints with Resend.

        Requires the user to have an active Google/Gmail integration configured.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (SendEmailRequest): Request schema for sending an email Example: {'bcc':
            ['bcc@example.com'], 'body': 'Thank you for the meeting today...', 'cc':
            ['cc@example.com'], 'html_body': '<p>Thank you for the meeting today...</p>', 'reply_to':
            'sender@example.com', 'subject': 'Meeting Follow-up', 'to_email':
            'recipient@example.com'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SendEmailResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SendEmailRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | SendEmailResponse]:
    """Send email via user's Gmail account

     Send an email on behalf of the authenticated user using their connected Gmail account.

        **User Email Service**: Sends emails through the user's personal Gmail via Google Gmail API.
        This is NOT for system emails - those use the separate system-emails endpoints with Resend.

        Requires the user to have an active Google/Gmail integration configured.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (SendEmailRequest): Request schema for sending an email Example: {'bcc':
            ['bcc@example.com'], 'body': 'Thank you for the meeting today...', 'cc':
            ['cc@example.com'], 'html_body': '<p>Thank you for the meeting today...</p>', 'reply_to':
            'sender@example.com', 'subject': 'Meeting Follow-up', 'to_email':
            'recipient@example.com'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SendEmailResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: SendEmailRequest,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | SendEmailResponse | None:
    """Send email via user's Gmail account

     Send an email on behalf of the authenticated user using their connected Gmail account.

        **User Email Service**: Sends emails through the user's personal Gmail via Google Gmail API.
        This is NOT for system emails - those use the separate system-emails endpoints with Resend.

        Requires the user to have an active Google/Gmail integration configured.

    Args:
        x_current_organization (str | Unset): Current organization ID
        body (SendEmailRequest): Request schema for sending an email Example: {'bcc':
            ['bcc@example.com'], 'body': 'Thank you for the meeting today...', 'cc':
            ['cc@example.com'], 'html_body': '<p>Thank you for the meeting today...</p>', 'reply_to':
            'sender@example.com', 'subject': 'Meeting Follow-up', 'to_email':
            'recipient@example.com'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SendEmailResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_current_organization=x_current_organization,
        )
    ).parsed
