"""Explicit cloud dispatch for computer commands."""

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
        elif action == "get":
            from celesto._providers.cloud import get_cloud_computer

            data = get_cloud_computer(args.computer_id)
            if json_output:
                emit_json(command, 0, data=data)
            else:
                for key, value in data.items():
                    print(f"{key}: {value}")
        elif action == "run":
            handle = CloudComputer.get(args.computer_id)
            result = handle.run(args.run_command, timeout=args.timeout)
            return _emit_command_result(command, result, json_output=json_output)
        elif action == "stop":
            from celesto._providers.cloud import stop_cloud_computer

            data = stop_cloud_computer(args.computer_id)
            if json_output:
                emit_json(command, 0, data=data)
            else:
                print(f"Stopped cloud computer '{args.computer_id}'.")
        elif action == "start":
            if not getattr(args, "computer_id", None):
                raise ValueError(
                    "A computer id is required to resume a cloud computer; "
                    "run 'celesto computer create --cloud' to create a new one."
                )
            from celesto._providers.cloud import start_cloud_computer

            data = start_cloud_computer(args.computer_id)
            if json_output:
                emit_json(command, 0, data=data)
            else:
                print(f"Started cloud computer '{args.computer_id}'.")
        elif action == "port_publish":
            handle = CloudComputer.get(args.computer_id)
            result = handle.publish_port(args.port_number)
            if json_output:
                emit_json(command, 0, data=result.model_dump())
            else:
                print(result.url or f"Published port {args.port_number}.")
        elif action == "port_list":
            handle = CloudComputer.get(args.computer_id)
            results = handle.published_ports()
            if json_output:
                emit_json(command, 0, data={"ports": [r.model_dump() for r in results]})
            else:
                for r in results:
                    print(f"{r.port}\t{r.status}\t{r.url or ''}")
                if not results:
                    print("No published ports.")
        elif action == "port_unpublish":
            handle = CloudComputer.get(args.computer_id)
            result = handle.unpublish_port(args.port_number)
            if json_output:
                emit_json(command, 0, data=result.model_dump())
            else:
                print(f"Unpublished port {args.port_number}.")
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
        if isinstance(exc, ValueError) and str(exc).startswith("Set CELESTO_API_KEY"):
            exc = ValueError(
                "Cloud API key is missing. Run 'celesto auth login' to connect to Celesto Cloud."
            )
        return _emit_cli_error(command, 1, exc, json_output=json_output)
    finally:
        if handle is not None:
            handle.close()
