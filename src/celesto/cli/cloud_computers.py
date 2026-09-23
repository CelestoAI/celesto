"""Explicit cloud dispatch for computer commands."""

import os
import shlex
from types import SimpleNamespace

from celesto import CloudComputer


def run_cloud_computer(args: SimpleNamespace) -> int:
    from celesto.cli.main import _emit_cli_error, _emit_command_result
    from celesto.cli.output import emit_json

    action = args.computer_action
    command = f"computer.{action}"
    json_output = getattr(args, "json", False)
    handle = None
    try:
        if not os.environ.get("CELESTO_API_KEY", "").strip():
            raise ValueError(
                "Cloud API key is missing. Set CELESTO_API_KEY, then run "
                "'celesto computer list --cloud' to check access."
            )
        if action == "create":
            handle = CloudComputer(lifetime="persistent", startup_timeout=args.boot_timeout)
            handle.start()
            if json_output:
                emit_json(command, 0, data={"computer_id": handle.id, "provider": "cloud"})
            else:
                print(f"Created cloud computer '{handle.id}'.")
        elif action == "list":
            from celesto._providers.cloud import list_cloud_computers

            rows, possibly_truncated = list_cloud_computers(limit=args.limit)
            if json_output:
                emit_json(
                    command,
                    0,
                    data={
                        "computers": rows,
                        "provider": "cloud",
                        "limit": args.limit,
                        "possibly_truncated": possibly_truncated,
                    },
                )
            else:
                for row in rows:
                    print(f"{row['computer_id']}\t{row['status']}")
                if not rows:
                    print("No cloud computers found.")
                if possibly_truncated:
                    print(
                        f"More cloud computers may exist. Run "
                        f"'celesto computer list --cloud --limit {args.limit * 2}' "
                        "to request more."
                    )
        elif action in {"delete", "terminal", "exec"}:
            handle = CloudComputer.get(args.computer_id)
            if action == "delete":
                handle.delete()
                print(f"Deleted cloud computer '{args.computer_id}'.")
            elif action == "terminal":
                handle.terminal().attach()
                return 0
            else:
                result = handle.run(shlex.join(args.command), timeout=args.timeout)
                return _emit_command_result(command, result, json_output=json_output)
        else:
            raise ValueError(
                f"Cloud '{action}' is not available in this CLI; "
                "run 'celesto computer list --cloud' to find cloud computers."
            )
        return 0
    except Exception as exc:
        return _emit_cli_error(command, 1, exc, json_output=json_output)
    finally:
        if handle is not None:
            handle.close()
