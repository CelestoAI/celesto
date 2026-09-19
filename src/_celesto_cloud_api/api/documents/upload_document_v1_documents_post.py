from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.body_upload_document_v1_documents_post import (
    BodyUploadDocumentV1DocumentsPost,
)
from ...models.document_response import DocumentResponse
from ...models.http_validation_error import HTTPValidationError
from typing import cast


def _get_kwargs(
    *,
    body: BodyUploadDocumentV1DocumentsPost,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/documents",
    }

    _kwargs["files"] = body.to_multipart()

    headers["Content-Type"] = "multipart/form-data; boundary=+++"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DocumentResponse | HTTPValidationError | None:
    if response.status_code == 201:
        response_201 = DocumentResponse.from_dict(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DocumentResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: BodyUploadDocumentV1DocumentsPost,
) -> Response[DocumentResponse | HTTPValidationError]:
    """Upload a document

     Upload a document with flexible scope support.

    Supports three access patterns:
    1. Organization-level: scope=organization, organization_id=<id>
    2. Project-level: scope=project, project_id=<id>
    3. User-level: scope=user (uses personal organization)

    Args:
        body (BodyUploadDocumentV1DocumentsPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DocumentResponse | HTTPValidationError]
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
    body: BodyUploadDocumentV1DocumentsPost,
) -> DocumentResponse | HTTPValidationError | None:
    """Upload a document

     Upload a document with flexible scope support.

    Supports three access patterns:
    1. Organization-level: scope=organization, organization_id=<id>
    2. Project-level: scope=project, project_id=<id>
    3. User-level: scope=user (uses personal organization)

    Args:
        body (BodyUploadDocumentV1DocumentsPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DocumentResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: BodyUploadDocumentV1DocumentsPost,
) -> Response[DocumentResponse | HTTPValidationError]:
    """Upload a document

     Upload a document with flexible scope support.

    Supports three access patterns:
    1. Organization-level: scope=organization, organization_id=<id>
    2. Project-level: scope=project, project_id=<id>
    3. User-level: scope=user (uses personal organization)

    Args:
        body (BodyUploadDocumentV1DocumentsPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DocumentResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: BodyUploadDocumentV1DocumentsPost,
) -> DocumentResponse | HTTPValidationError | None:
    """Upload a document

     Upload a document with flexible scope support.

    Supports three access patterns:
    1. Organization-level: scope=organization, organization_id=<id>
    2. Project-level: scope=project, project_id=<id>
    3. User-level: scope=user (uses personal organization)

    Args:
        body (BodyUploadDocumentV1DocumentsPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DocumentResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
