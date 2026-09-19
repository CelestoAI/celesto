from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.outbound_generation_request import OutboundGenerationRequest
from ...models.outbound_generation_response import OutboundGenerationResponse
from typing import cast


def _get_kwargs(
    *,
    body: OutboundGenerationRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/ai/outbound/generate",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | OutboundGenerationResponse | None:
    if response.status_code == 200:
        response_200 = OutboundGenerationResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | OutboundGenerationResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: OutboundGenerationRequest,
) -> Response[HTTPValidationError | OutboundGenerationResponse]:
    """Generate personalized outbound message

     Generate a personalized email or LinkedIn DM based on persona data

    Args:
        body (OutboundGenerationRequest): Request schema for generating outbound messages.
            Example: {'channel': 'email', 'cta': 'Would you be open to a quick 15-min call next
            week?', 'goal': 'book a 15-min demo', 'persona': {'company': 'Nimbus Data', 'name':
            'Jordan Lee', 'problems': ['spread across tools', 'slow handoffs'], 'recent_post': 'revops
            tooling debt', 'role': 'VP Sales'}, 'tone': 'professional yet friendly', 'value_props':
            'AI-powered sales automation, real-time insights, seamless CRM integration'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OutboundGenerationResponse]
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
    body: OutboundGenerationRequest,
) -> HTTPValidationError | OutboundGenerationResponse | None:
    """Generate personalized outbound message

     Generate a personalized email or LinkedIn DM based on persona data

    Args:
        body (OutboundGenerationRequest): Request schema for generating outbound messages.
            Example: {'channel': 'email', 'cta': 'Would you be open to a quick 15-min call next
            week?', 'goal': 'book a 15-min demo', 'persona': {'company': 'Nimbus Data', 'name':
            'Jordan Lee', 'problems': ['spread across tools', 'slow handoffs'], 'recent_post': 'revops
            tooling debt', 'role': 'VP Sales'}, 'tone': 'professional yet friendly', 'value_props':
            'AI-powered sales automation, real-time insights, seamless CRM integration'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OutboundGenerationResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: OutboundGenerationRequest,
) -> Response[HTTPValidationError | OutboundGenerationResponse]:
    """Generate personalized outbound message

     Generate a personalized email or LinkedIn DM based on persona data

    Args:
        body (OutboundGenerationRequest): Request schema for generating outbound messages.
            Example: {'channel': 'email', 'cta': 'Would you be open to a quick 15-min call next
            week?', 'goal': 'book a 15-min demo', 'persona': {'company': 'Nimbus Data', 'name':
            'Jordan Lee', 'problems': ['spread across tools', 'slow handoffs'], 'recent_post': 'revops
            tooling debt', 'role': 'VP Sales'}, 'tone': 'professional yet friendly', 'value_props':
            'AI-powered sales automation, real-time insights, seamless CRM integration'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OutboundGenerationResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: OutboundGenerationRequest,
) -> HTTPValidationError | OutboundGenerationResponse | None:
    """Generate personalized outbound message

     Generate a personalized email or LinkedIn DM based on persona data

    Args:
        body (OutboundGenerationRequest): Request schema for generating outbound messages.
            Example: {'channel': 'email', 'cta': 'Would you be open to a quick 15-min call next
            week?', 'goal': 'book a 15-min demo', 'persona': {'company': 'Nimbus Data', 'name':
            'Jordan Lee', 'problems': ['spread across tools', 'slow handoffs'], 'recent_post': 'revops
            tooling debt', 'role': 'VP Sales'}, 'tone': 'professional yet friendly', 'value_props':
            'AI-powered sales automation, real-time insights, seamless CRM integration'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OutboundGenerationResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
