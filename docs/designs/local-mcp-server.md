# Local MCP server for Celesto

Status: Expanded locally; external user validation pending
Date: 2026-10-07

## Goal

Let an AI agent use a Celesto computer on the user's machine through MCP tools. The first complete task is to create a sandbox, run a command, inspect its output, and delete it, without teaching the agent Celesto CLI syntax.

## What we know

- Today's workflow uses the CLI to create a sandbox and run commands.
- The first target is the user's own machine, not Celesto Cloud.
- The first implementation also exposes local file, snapshot, environment, port-forwarding, browser-session, and desktop lifecycle operations through MCP.
- Demand for the MCP integration has not yet been validated with an external user's observed workflow.

## Proposed user path

1. Install Celesto and complete the existing local setup.
1. Add a local Celesto MCP server to an MCP client. The client launches `celesto mcp start` over stdio.
1. The agent discovers local computer lifecycle and inspection tools, file transfer, snapshots, environment and port management, browser sessions, and desktop sessions.
1. A tool returns structured sandbox IDs, state, stdout, stderr, exit code, and timing or timeout information where relevant. Tool errors include a concise recovery action.
1. The user can inspect and manage the same sandboxes through the CLI. Sandboxes persist when the MCP process exits; deletion is explicit.

## Product boundaries

- Local execution only. No Cloud credentials, remote MCP endpoint, host folder sharing, or arbitrary VM configuration.
- Creation starts a published Ubuntu image, so local image building does not require Docker. The first tool accepts a name and no VM tuning options.
- The server uses the persistent local inventory shared by the CLI. It calls Celesto's Python service and facade directly; it does not shell out to `celesto` or create a second inventory.
- Tool results distinguish a command that exits nonzero from a tool failure. Command execution is limited to 300 seconds. Each output stream is retained up to 16,384 characters, with truncation flags, the selected timeout, and elapsed time in the result.
- No sandbox should be deleted merely because an MCP client disconnects or retries. Deletion is an explicit, clearly described tool action.
- The first transport is stdio. Keep protocol output clean; diagnostics go to stderr.

## Integration points

- Add `celesto mcp start` as a resource command, following the CLI's noun-verb rule.
- Reuse `CLIService` in `src/celesto/cli/service.py` for the shared SQLite inventory and sandbox handles.
- Reuse the existing facade and manager for lifecycle and command execution. Keep the MCP adapter thin and typed.
- Add the MCP Python SDK as an optional dependency if practical, so users who never enable MCP do not pay its install cost. Validate this against the actual client setup experience.

## Acceptance flow

The end-to-end test launches the MCP server as a subprocess, connects with an MCP client, lists tools, creates a named sandbox, writes and reads a file, lists the sandbox through the CLI and a second MCP process, deletes it through MCP, and confirms through the CLI that it is gone. It also checks nonzero exit, nonexistent sandbox, timeout, stop/start, and output truncation. Set `CELESTO_RUN_MCP_E2E=1` to run it on a prepared machine. The test saves its protocol transcript under pytest's temporary directory.

## Release order

1. Prove the full local command flow with one MCP client and an end-to-end test. Done.
1. Ship copyable Claude Code setup instructions plus a generic stdio configuration example. Done.
1. Observe an external user connect an agent without coaching. Record where setup or tool descriptions fail.
1. Observe an external user connect an agent without coaching. Record where setup or tool descriptions fail; evaluate Cloud and remote transport separately.

## Open decisions

- Claude Code is the first documented client; client-specific setup can expand based on user feedback.
- Should sandbox creation start the computer automatically, matching the simplest agent flow, or expose a separate start step?
- What default execution timeout and output cap best match real agent tasks?

## Validation assignment

Watch one agent builder connect Celesto to their existing MCP client using only the instructions. Ask them to complete a small command task, then note every point where they reach for the CLI or ask for help. This tests whether MCP actually reduces integration effort.
