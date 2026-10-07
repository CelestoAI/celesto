# Hosted MCP access to Celesto Cloud

Status: Self-hostable HTTP gateway implemented; Celesto production deployment and OAuth pending
Date: 2026-10-07

## Goal

Let an MCP client connect to a Celesto endpoint over the internet and manage Cloud computers without installing Celesto on the same machine as the agent.

## User flow

1. The user signs in to Celesto and gets a personal Celesto API key.
1. They add the Celesto MCP endpoint URL to an MCP client.
1. The client sends the key as an `Authorization: Bearer` header over HTTPS.
1. The MCP gateway validates the key with the Celesto Cloud API, then passes that caller's key to the Cloud API for each Cloud operation.
1. The user can create, inspect, run commands on, start, stop, delete, and publish ports for their Cloud computers.

## Architecture

- The endpoint uses MCP Streamable HTTP and is stateless between requests.
- The remote server registers only `cloud_computer_*` tools. It never exposes local VM, host file, browser, or desktop operations.
- Authentication runs at the HTTP boundary. Missing or invalid API keys receive `401`; keys are validated against the Cloud user-info endpoint before MCP messages are handled.
- The gateway forwards the validated caller key only to the configured Celesto Cloud API origin. It does not read a server-wide `CELESTO_API_KEY` for remote requests.
- Cloud-create tools require a caller-provided idempotency key and reuse it when retrying the same request, preventing duplicate persistent allocations after a lost response.
- The existing stdio server remains the local integration path. It continues to use `celesto auth login` credentials on the user's machine.
- The implemented remote auth option is static API-key bearer auth. Clients must support custom HTTP headers for this mode. A Celesto OAuth authorization flow is required before calling this universally compatible across remote clients.

## Implementation slices

1. Extract Cloud tool registration so both stdio and HTTP servers use the same Cloud tool definitions.
1. Add a Cloud-only HTTP server with per-request bearer-key validation and no local tools.
1. Add `celesto mcp serve` with loopback as its default bind address and explicit allowed-host configuration.
1. Document the remote client config and the self-hosted deployment requirements. Done.
1. Add ingress rate and request-size limits, deploy behind TLS at `https://mcp.celesto.ai/mcp`, add OAuth sign-in and short-lived scoped MCP access tokens, then publish client setup instructions and registry metadata.

## Security requirements

- Never put API keys in tool arguments, URLs, results, or logs.
- Never return the API key or auth response body to the agent.
- Validate each remote HTTP request before forwarding the key to Cloud operations. Add ingress rate limits and request-size limits before a public launch.
- Do not expose loopback/local computer tools from the remote endpoint.
- Bind local development to loopback by default. Public deployments must use HTTPS at a trusted reverse proxy and an explicit allowed hostname.
- Preserve the caller's API-key scope and organization access. Do not use a shared Celesto service key for caller operations.

## Deployment boundary

This repository contains the Celesto Python package and generated Cloud client, not the deployed Cloud API service or its identity-provider configuration. The package can run the HTTP gateway, but publishing the production URL, configuring TLS and DNS, and implementing Celesto OAuth require the Cloud service/deployment repository and its auth configuration.

## Verification and rollout

- Verify that an authenticated HTTP MCP client can list and call the Cloud tools.
- Verify missing, malformed, invalid, revoked, and wrong-organization keys are rejected without leaking credential data.
- Verify the remote endpoint never lists local/browser/desktop tools.
- Deploy behind HTTPS, test with Claude Code and at least one other MCP client, then publish `https://mcp.celesto.ai/mcp`.
- Keep stdio available for local sandbox and development workflows.
