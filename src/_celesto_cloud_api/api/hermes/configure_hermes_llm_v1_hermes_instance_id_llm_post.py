from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.hermes_llm_config_request import HermesLLMConfigRequest
from ...models.hermes_setup_step_response import HermesSetupStepResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast


def _get_kwargs(
    instance_id: str,
    *,
    body: HermesLLMConfigRequest,
    x_current_organization: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_current_organization, Unset):
        headers["x-current-organization"] = x_current_organization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/hermes/{instance_id}/llm".format(
            instance_id=quote(str(instance_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | HermesSetupStepResponse | None:
    if response.status_code == 202:
        response_202 = HermesSetupStepResponse.from_dict(response.json())

        return response_202

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | HermesSetupStepResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    instance_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: HermesLLMConfigRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | HermesSetupStepResponse]:
    """Configure the Hermes LLM provider

    Args:
        instance_id (str):
        x_current_organization (str | Unset): Current organization ID
        body (HermesLLMConfigRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | HermesSetupStepResponse]
    """

    kwargs = _get_kwargs(
        instance_id=instance_id,
        body=body,
        x_current_organization=x_current_organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    instance_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: HermesLLMConfigRequest,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | HermesSetupStepResponse | None:
    """Configure the Hermes LLM provider

    Args:
        instance_id (str):
        x_current_organization (str | Unset): Current organization ID
        body (HermesLLMConfigRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | HermesSetupStepResponse
    """

    return sync_detailed(
        instance_id=instance_id,
        client=client,
        body=body,
        x_current_organization=x_current_organization,
    ).parsed


async def asyncio_detailed(
    instance_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: HermesLLMConfigRequest,
    x_current_organization: str | Unset = UNSET,
) -> Response[HTTPValidationError | HermesSetupStepResponse]:
    """Configure the Hermes LLM provider

    Args:
        instance_id (str):
        x_current_organization (str | Unset): Current organization ID
        body (HermesLLMConfigRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | HermesSetupStepResponse]
    """

    kwargs = _get_kwargs(
        instance_id=instance_id,
        body=body,
        x_current_organization=x_current_organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    instance_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: HermesLLMConfigRequest,
    x_current_organization: str | Unset = UNSET,
) -> HTTPValidationError | HermesSetupStepResponse | None:
    """Configure the Hermes LLM provider

    Args:
        instance_id (str):
        x_current_organization (str | Unset): Current organization ID
        body (HermesLLMConfigRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | HermesSetupStepResponse
    """

    return (
        await asyncio_detailed(
            instance_id=instance_id,
            client=client,
            body=body,
            x_current_organization=x_current_organization,
        )
    ).parsed
