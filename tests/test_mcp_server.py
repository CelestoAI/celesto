"""Exercise the public MCP process protocol without starting a virtual machine."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest
from mcp import Client, StdioServerParameters


def _server(data_dir):
    return StdioServerParameters(
        command=sys.executable,
        args=["-c", "from celesto.cli.main import main; raise SystemExit(main())", "mcp", "start"],
        env={"CELESTO_DATA_DIR": str(data_dir)},
    )


@pytest.mark.asyncio
async def test_local_mcp_exposes_computer_tools(tmp_path):
    async with Client(_server(tmp_path)) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools.tools}
        assert names == {
            "browser_create",
            "browser_list",
            "browser_logs",
            "browser_open",
            "browser_stop",
            "computer_create",
            "computer_delete",
            "computer_doctor",
            "computer_download",
            "computer_env_list",
            "computer_env_set",
            "computer_env_unset",
            "computer_exec",
            "computer_info",
            "computer_list",
            "computer_logs",
            "computer_pause",
            "computer_port_close",
            "computer_port_expose",
            "computer_port_list",
            "computer_resume",
            "computer_snapshot_create",
            "computer_snapshot_delete",
            "computer_snapshot_list",
            "computer_snapshot_restore",
            "computer_start",
            "computer_stop",
            "computer_templates",
            "computer_upload",
            "desktop_create",
            "desktop_list",
            "desktop_open",
            "desktop_stop",
        }
        by_name = {tool.name: tool for tool in tools.tools}
        assert by_name["computer_list"].annotations.read_only_hint is True
        assert by_name["computer_delete"].annotations.destructive_hint is True
        result = await client.call_tool("computer_list", {})
        assert not result.is_error
        assert result.structured_content == {"computers": []}
        (tmp_path / "mcp-transcript.json").write_text(
            json.dumps({"tools": sorted(names), "list": result.structured_content}, indent=2)
        )


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_agent_can_use_local_computer_and_cli_can_see_it(tmp_path):
    if os.environ.get("CELESTO_RUN_MCP_E2E") != "1":
        pytest.skip("Set CELESTO_RUN_MCP_E2E=1 on a prepared local computer")
    name = "sbx-mcp-e2e"
    transcript = []
    async with Client(_server(tmp_path)) as client:
        created_ok = False
        try:
            created = await client.call_tool("computer_create", {"name": name})
            transcript.append({"create": created.structured_content})
            assert not created.is_error, created.content
            created_ok = True

            written = await client.call_tool(
                "computer_exec", {"name": name, "command": "printf celesto-mcp > /tmp/mcp-proof"}
            )
            transcript.append({"write": written.structured_content})
            assert written.structured_content["exit_code"] == 0

            read = await client.call_tool(
                "computer_exec", {"name": name, "command": "cat /tmp/mcp-proof"}
            )
            transcript.append({"read": read.structured_content})
            assert read.structured_content["stdout"].strip() == "celesto-mcp"
            assert read.structured_content["timeout_seconds"] == 30
            assert read.structured_content["duration_ms"] >= 0

            large = await client.call_tool(
                "computer_exec", {"name": name, "command": "yes x | head -c 20000"}
            )
            transcript.append({"large": {"length": len(large.structured_content["stdout"])}})
            assert len(large.structured_content["stdout"]) == 16_384
            assert large.structured_content["stdout_truncated"] is True

            nonzero = await client.call_tool("computer_exec", {"name": name, "command": "exit 7"})
            transcript.append({"nonzero": nonzero.structured_content})
            assert not nonzero.is_error
            assert nonzero.structured_content["exit_code"] == 7

            missing = await client.call_tool(
                "computer_exec", {"name": "sbx-does-not-exist", "command": "true"}
            )
            transcript.append({"missing_error": missing.is_error})
            assert missing.is_error

            timed_out = await client.call_tool(
                "computer_exec", {"name": name, "command": "sleep 5", "timeout": 1}
            )
            transcript.append({"timeout_error": timed_out.is_error})
            assert timed_out.is_error
            assert "1 second" in timed_out.content[0].text

            stopped = await client.call_tool("computer_stop", {"name": name})
            transcript.append({"stop": stopped.structured_content})
            assert stopped.structured_content["state"] == "stopped"
            started = await client.call_tool("computer_start", {"name": name})
            transcript.append({"start": started.structured_content})
            assert started.structured_content["state"] == "running"

            listed = await client.call_tool("computer_list", {})
            transcript.append({"list": listed.structured_content})
            assert any(item["name"] == name for item in listed.structured_content["computers"])
            cli = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from celesto.cli.main import main; raise SystemExit(main())",
                    "computer",
                    "list",
                    "--all",
                    "--json",
                ],
                env={**os.environ, "CELESTO_DATA_DIR": str(tmp_path)},
                capture_output=True,
                text=True,
                check=True,
            )
            transcript.append({"cli_list": json.loads(cli.stdout)})
            assert name in cli.stdout
            async with Client(_server(tmp_path)) as restarted:
                persisted = await restarted.call_tool("computer_list", {})
                transcript.append({"restart_list": persisted.structured_content})
                assert any(
                    item["name"] == name for item in persisted.structured_content["computers"]
                )
        finally:
            try:
                if created_ok:
                    deleted = await client.call_tool("computer_delete", {"name": name})
                    transcript.append({"delete": deleted.structured_content})
                    assert not deleted.is_error, deleted.content
            finally:
                (tmp_path / "mcp-e2e-transcript.json").write_text(json.dumps(transcript, indent=2))
    async with Client(_server(tmp_path)) as client:
        listed = await client.call_tool("computer_list", {})
        assert all(item["name"] != name for item in listed.structured_content["computers"])
    cli_after = subprocess.run(
        [
            sys.executable,
            "-c",
            "from celesto.cli.main import main; raise SystemExit(main())",
            "computer",
            "list",
            "--all",
            "--json",
        ],
        env={**os.environ, "CELESTO_DATA_DIR": str(tmp_path)},
        capture_output=True,
        text=True,
        check=True,
    )
    assert name not in cli_after.stdout
