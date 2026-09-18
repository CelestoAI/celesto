from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.check_gmail_integration_v1_user_emails_integration_status_get_response_check_gmail_integration_v1_user_emails_integration_status_get import (
    CheckGmailIntegrationV1UserEmailsIntegrationStatusGetResponseCheckGmailIntegrationV1UserEmailsIntegrationStatusGet,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    *,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/user-emails/integration-status",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CheckGmailIntegrationV1UserEmailsIntegrationStatusGetResponseCheckGmailIntegrationV1UserEmailsIntegrationStatusGet
    | HTTPValidationError
    | None
):
    if response.status_code == 200:
        response_200 = CheckGmailIntegrationV1UserEmailsIntegrationStatusGetResponseCheckGmailIntegrationV1UserEmailsIntegrationStatusGet.from_dict(
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
    CheckGmailIntegrationV1UserEmailsIntegrationStatusGetResponseCheckGmailIntegrationV1UserEmailsIntegrationStatusGet
    | HTTPValidationError
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    CheckGmailIntegrationV1UserEmailsIntegrationStatusGetResponseCheckGmailIntegrationV1UserEmailsIntegrationStatusGet
    | HTTPValidationError
]:
    """Check user's Gmail integration status

     Check if the authenticated user has an active Gmail integration for sending emails.

        **User Email Service**: Validates the user's personal Gmail connection status.
        This endpoint helps determine if the user can send emails via their Gmail account.

    Args:
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CheckGmailIntegrationV1UserEmailsIntegrationStatusGetResponseCheckGmailIntegrationV1UserEmailsIntegrationStatusGet | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> (
    CheckGmailIntegrationV1UserEmailsIntegrationStatusGetResponseCheckGmailIntegrationV1UserEmailsIntegrationStatusGet
    | HTTPValidationError
    | None
):
    """Check user's Gmail integration status

     Check if the authenticated user has an active Gmail integration for sending emails.

        **User Email Service**: Validates the user's personal Gmail connection status.
        This endpoint helps determine if the user can send emails via their Gmail account.

    Args:
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CheckGmailIntegrationV1UserEmailsIntegrationStatusGetResponseCheckGmailIntegrationV1UserEmailsIntegrationStatusGet | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> Response[
    CheckGmailIntegrationV1UserEmailsIntegrationStatusGetResponseCheckGmailIntegrationV1UserEmailsIntegrationStatusGet
    | HTTPValidationError
]:
    """Check user's Gmail integration status

     Check if the authenticated user has an active Gmail integration for sending emails.

        **User Email Service**: Validates the user's personal Gmail connection status.
        This endpoint helps determine if the user can send emails via their Gmail account.

    Args:
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CheckGmailIntegrationV1UserEmailsIntegrationStatusGetResponseCheckGmailIntegrationV1UserEmailsIntegrationStatusGet | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    x_current_organization: str | Unset = UNSET,
) -> (
    CheckGmailIntegrationV1UserEmailsIntegrationStatusGetResponseCheckGmailIntegrationV1UserEmailsIntegrationStatusGet
    | HTTPValidationError
    | None
):
    """Check user's Gmail integration status

     Check if the authenticated user has an active Gmail integration for sending emails.

        **User Email Service**: Validates the user's personal Gmail connection status.
        This endpoint helps determine if the user can send emails via their Gmail account.

    Args:
        x_current_organization (str | Unset): Current organization ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CheckGmailIntegrationV1UserEmailsIntegrationStatusGetResponseCheckGmailIntegrationV1UserEmailsIntegrationStatusGet | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            x_current_organization=x_current_organization,
        )
    ).parsed
