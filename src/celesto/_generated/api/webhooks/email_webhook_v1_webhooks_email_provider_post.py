from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.email_webhook_v1_webhooks_email_provider_post_body import (
    EmailWebhookV1WebhooksEmailProviderPostBody,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    provider: str,
    *,
    body: EmailWebhookV1WebhooksEmailProviderPostBody | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/webhooks/email/{provider}".format(
            provider=quote(str(provider), safe=""),
        ),
    }

    if not isinstance(body, Unset):
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
    provider: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmailWebhookV1WebhooksEmailProviderPostBody | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Email Webhook

     Capture email provider events (delivered, bounce, complaint, etc.).

    Only supports Resend for now. Requires a shared secret header for auth and applies
    basic abuse mitigations (size cap, idempotency via body hash).

    Expected payload format:
    {
        "type": "email.delivery_delayed",
        "created_at": "2025-08-28T22:54:59.973Z",
        "data": {
            "email_id": "608db242-49e6-4d99-a361-bf7de10825b0",
            "from": "no-reply@celesto.ai",
            "to": ["test@example.com"],
            "subject": "Test Subject"
        }
    }

    Args:
        provider (str): Email provider e.g. resend, sendgrid, ses
        body (EmailWebhookV1WebhooksEmailProviderPostBody | Unset): JSON payload from email
            provider

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        provider=provider,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    provider: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmailWebhookV1WebhooksEmailProviderPostBody | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Email Webhook

     Capture email provider events (delivered, bounce, complaint, etc.).

    Only supports Resend for now. Requires a shared secret header for auth and applies
    basic abuse mitigations (size cap, idempotency via body hash).

    Expected payload format:
    {
        "type": "email.delivery_delayed",
        "created_at": "2025-08-28T22:54:59.973Z",
        "data": {
            "email_id": "608db242-49e6-4d99-a361-bf7de10825b0",
            "from": "no-reply@celesto.ai",
            "to": ["test@example.com"],
            "subject": "Test Subject"
        }
    }

    Args:
        provider (str): Email provider e.g. resend, sendgrid, ses
        body (EmailWebhookV1WebhooksEmailProviderPostBody | Unset): JSON payload from email
            provider

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        provider=provider,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    provider: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmailWebhookV1WebhooksEmailProviderPostBody | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Email Webhook

     Capture email provider events (delivered, bounce, complaint, etc.).

    Only supports Resend for now. Requires a shared secret header for auth and applies
    basic abuse mitigations (size cap, idempotency via body hash).

    Expected payload format:
    {
        "type": "email.delivery_delayed",
        "created_at": "2025-08-28T22:54:59.973Z",
        "data": {
            "email_id": "608db242-49e6-4d99-a361-bf7de10825b0",
            "from": "no-reply@celesto.ai",
            "to": ["test@example.com"],
            "subject": "Test Subject"
        }
    }

    Args:
        provider (str): Email provider e.g. resend, sendgrid, ses
        body (EmailWebhookV1WebhooksEmailProviderPostBody | Unset): JSON payload from email
            provider

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        provider=provider,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    provider: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmailWebhookV1WebhooksEmailProviderPostBody | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Email Webhook

     Capture email provider events (delivered, bounce, complaint, etc.).

    Only supports Resend for now. Requires a shared secret header for auth and applies
    basic abuse mitigations (size cap, idempotency via body hash).

    Expected payload format:
    {
        "type": "email.delivery_delayed",
        "created_at": "2025-08-28T22:54:59.973Z",
        "data": {
            "email_id": "608db242-49e6-4d99-a361-bf7de10825b0",
            "from": "no-reply@celesto.ai",
            "to": ["test@example.com"],
            "subject": "Test Subject"
        }
    }

    Args:
        provider (str): Email provider e.g. resend, sendgrid, ses
        body (EmailWebhookV1WebhooksEmailProviderPostBody | Unset): JSON payload from email
            provider

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            provider=provider,
            client=client,
            body=body,
        )
    ).parsed
