# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""``celesto computer ssh-key add|remove|list`` (D-13).

Choose which of your SSH keys a computer may sign with. Only public keys and
fingerprints are stored; the private key stays in your SSH agent.
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from rich.table import Table

from celesto.cli.output import console_stdout, emit_json, render_empty, render_error
from celesto.credentials import ssh as cssh
from celesto.exceptions import VMNotFoundError


class SshKeyError(Exception):
    """A user-facing ssh-key error whose message includes the recovery."""


def _private_path(pub_arg: str) -> str:
    return pub_arg[: -len(".pub")] if pub_arg.endswith(".pub") else pub_arg


def _read_key(vm_id: str, path_arg: str) -> cssh.PublicKey:
    path = Path(path_arg).expanduser()
    try:
        text = path.read_text(errors="replace")
    except FileNotFoundError:
        raise SshKeyError(
            f"Can't find the key file '{path_arg}'. Run 'ls ~/.ssh' to see your keys."
        ) from None
    except OSError as exc:
        raise SshKeyError(f"Can't read the key file '{path_arg}': {exc.strerror}.") from None
    if cssh.looks_like_private_key(text):
        raise SshKeyError(
            f"'{path_arg}' is a private key. Pass its public key instead: "
            f"'celesto computer ssh-key add {vm_id} {path_arg}.pub'."
        )
    try:
        return cssh.parse_public_key(text)
    except ValueError:
        raise SshKeyError(
            f"'{path_arg}' isn't an SSH public key. Pass a '.pub' file, for example "
            f"'celesto computer ssh-key add {vm_id} ~/.ssh/id_ed25519.pub'."
        ) from None


def _check_host_agent(vm_id: str, path_arg: str, key: cssh.PublicKey) -> None:
    loaded = cssh.host_agent_fingerprints(os.environ.get("SSH_AUTH_SOCK"))
    private = _private_path(path_arg)
    retry = f"celesto computer ssh-key add {vm_id} {path_arg}"
    if loaded is None:
        raise SshKeyError(
            "No SSH agent is running in this terminal. Run 'eval \"$(ssh-agent)\"' and "
            f"'ssh-add {private}', then run '{retry}' again."
        )
    if key.fingerprint not in loaded:
        raise SshKeyError(
            f"Your SSH agent doesn't have the key '{path_arg}' loaded. "
            f"Run 'ssh-add {private}', then run '{retry}' again."
        )


def _key_row(fingerprint: str, line: str) -> dict[str, str]:
    try:
        key = cssh.parse_public_key(line)
        return {"fingerprint": fingerprint, "type": key.key_type, "comment": key.comment}
    except ValueError:
        return {"fingerprint": fingerprint, "type": "", "comment": ""}


def run_ssh_key(args: SimpleNamespace) -> int:
    """Handle ``celesto computer ssh-key add|remove|list``."""
    from celesto.cli.main import _cli_state_manager

    action = args.ssh_key_action
    command_name = f"sandbox.ssh-key.{action}"
    json_output = bool(getattr(args, "json", False))
    vm_id = args.vm_id
    try:
        state = _cli_state_manager()
        state.get_vm(vm_id)
        data: dict[str, Any]
        if action == "add":
            key = _read_key(vm_id, args.key)
            _check_host_agent(vm_id, args.key, key)
            added = state.add_ssh_key(vm_id, key.fingerprint, key.line())
            data = {
                "vm_id": vm_id,
                "fingerprint": key.fingerprint,
                "type": key.key_type,
                "comment": key.comment,
                "added": added,
            }
            if json_output:
                emit_json(command_name, 0, data=data)
            elif added:
                label = key.comment or key.key_type
                console_stdout().print(
                    f"'{vm_id}' can now sign with SSH key {key.fingerprint} ({label}). "
                    "The key itself stays in your SSH agent."
                )
            else:
                console_stdout().print(
                    f"'{vm_id}' can already sign with SSH key {key.fingerprint}."
                )
            return 0

        if action == "remove":
            target = args.key
            fingerprint = (
                target if target.startswith("SHA256:") else _read_key(vm_id, target).fingerprint
            )
            removed = state.remove_ssh_key(vm_id, fingerprint)
            data = {"vm_id": vm_id, "fingerprint": fingerprint, "removed": removed}
            if json_output:
                emit_json(command_name, 0, data=data)
            elif removed:
                console_stdout().print(f"'{vm_id}' can no longer sign with SSH key {fingerprint}.")
            else:
                console_stdout().print(
                    f"'{vm_id}' wasn't allowed to use SSH key {fingerprint}. "
                    f"Run 'celesto computer ssh-key list {vm_id}' to see its keys."
                )
            return 0

        rows = [_key_row(fp, line) for fp, line in state.list_ssh_keys(vm_id)]
        data = {"vm_id": vm_id, "keys": rows}
        if json_output:
            emit_json(command_name, 0, data=data)
        elif not rows:
            render_empty(
                "SSH Keys",
                f"'{vm_id}' can't sign with any of your SSH keys. Allow one with "
                f"'celesto computer ssh-key add {vm_id} ~/.ssh/id_ed25519.pub'.",
            )
        else:
            table = Table(title=f"SSH keys '{vm_id}' can sign with")
            table.add_column("Fingerprint")
            table.add_column("Type")
            table.add_column("Comment")
            for row in rows:
                table.add_row(row["fingerprint"], row["type"], row["comment"])
            console_stdout().print(table)
        return 0
    except (SshKeyError, VMNotFoundError) as exc:
        message = str(exc)
        code = "not_found" if isinstance(exc, VMNotFoundError) else "invalid_ssh_key"
        if json_output:
            emit_json(command_name, 1, error={"code": code, "message": message})
        else:
            render_error(message)
        return 1
