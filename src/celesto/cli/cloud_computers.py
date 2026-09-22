"""Explicit cloud dispatch for computer commands."""

from types import SimpleNamespace

from celesto import CloudComputer


def run_cloud_computer(args: SimpleNamespace) -> int:
    from celesto.cli.main import _emit_cli_error
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

            rows = list_cloud_computers()
            if json_output:
                emit_json(command, 0, data={"computers": rows, "provider": "cloud"})
            else:
                for row in rows:
                    print(f"{row['computer_id']}\t{row['status']}")
                if not rows:
                    print("No cloud computers found.")
        elif action == "get":
            from celesto._providers.cloud import get_cloud_computer

            data = get_cloud_computer(args.computer_id)
            if json_output:
                emit_json(command, 0, data=data)
            else:
                for key, value in data.items():
                    print(f"{key}: {value}")
        elif action == "run":
            import sys

            handle = CloudComputer.get(args.computer_id)
            result = handle.run(args.run_command, timeout=args.timeout)
            if json_output:
                emit_json(command, result.exit_code, data=result.model_dump())
            else:
                if result.stdout:
                    sys.stdout.write(result.stdout)
                if result.stderr:
                    sys.stderr.write(result.stderr)
            return result.exit_code
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
        elif action in {"delete", "terminal"}:
            handle = CloudComputer.get(args.computer_id)
            if action == "delete":
                handle.delete()
                print(f"Deleted cloud computer '{args.computer_id}'.")
            else:
                handle.terminal().attach()
                return 0
        else:
            raise ValueError(
                f"Cloud '{action}' is not available in this CLI; "
                "run 'celesto computer create --cloud' to create a cloud computer "
                "or use the cloud dashboard to manage it."
            )
        return 0
    except Exception as exc:
        return _emit_cli_error(command, 1, exc, json_output=json_output)
    finally:
        if handle is not None:
            handle.close()
