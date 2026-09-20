"""Adapt the existing local runtime without changing its storage or transports."""

import inspect
import shlex
from collections.abc import Iterator
from contextlib import suppress
from typing import TYPE_CHECKING, Any, NoReturn, cast

from celesto._connection_info import DisplayMode
from celesto._terminal import TerminalConnection, local_terminal_connection
from celesto.exceptions import BrowserSessionNotFoundError, CelestoError
from celesto.facade import Celesto
from celesto.types import (
    BrowserConnection,
    CommandEvent,
    CommandResult,
    DisplayConnection,
    PublishedPort,
)

if TYPE_CHECKING:
    from celesto.computer import _ComputerSandbox


class LocalProvider:
    def __init__(self, **options: Any) -> None:
        self._template = options.pop("template_id", None)
        self._connection_forwards: dict[int, int] = {}
        if self._template is not None:
            from celesto._connections import validate_template_options

            if self._template != "browser-agent":
                raise ValueError(
                    "Local template_id must be 'browser-agent'; omit it for a plain computer."
                )
            validate_template_options(options)
        inspect.signature(Celesto).bind(**options)
        self._options = options.copy()
        self._vm: Celesto | None = None
        self._desktop: _ComputerSandbox | None = None

    @property
    def _runtime(self) -> Celesto:
        if self._vm is None:
            raise CelestoError("This computer has not started; call start() first.")
        return self._vm

    @property
    def id(self) -> str | None:
        if self._desktop is not None:
            return self._desktop.computer_id
        return self._vm.vm_id if self._vm is not None else None

    def _runtime_options(self) -> dict[str, Any]:
        from celesto.cli.state import create_cli_state_manager
        from celesto.vm import resolve_data_dir

        options = self._options.copy()
        data_dir = resolve_data_dir(options.get("data_dir"))
        options["data_dir"] = data_dir
        options["state_manager"] = create_cli_state_manager(data_dir / "smolvm.db")
        return options

    def start(self) -> None:
        options = self._runtime_options()
        if self._template is not None:
            from celesto._connections import template_runtime_options

            options = template_runtime_options(options)
        self._vm = Celesto(**options)
        self._vm.start()
        if self._template is not None:
            from celesto._connections import probe_capabilities

            probe_capabilities(self._vm, "browser")

    def attach(self, computer_id: str) -> None:
        from celesto.computer import _ComputerSandbox

        options = self._runtime_options()
        state = options.get("state_manager")
        session = None
        if state is not None:
            with suppress(BrowserSessionNotFoundError):
                session = state.get_browser_session(computer_id)
        if session is not None and state is not None:
            config = state.get_browser_session_config(computer_id)
            if config.mode != "computer":
                raise ValueError(
                    f"'{computer_id}' is not a computer; run 'celesto computer list' to choose one."
                )
            unsupported = options.keys() - {
                "data_dir",
                "socket_dir",
                "ssh_key_path",
                "state_manager",
            }
            if unsupported:
                names = ", ".join(sorted(unsupported))
                raise ValueError(
                    f"Desktop computer '{computer_id}' does not accept {names} when reconnecting; "
                    "omit those options and retry."
                )
            self._desktop = cast(
                "_ComputerSandbox", _ComputerSandbox.from_id(computer_id, **options)
            )
            self._vm = self._desktop.vm
        else:
            self._vm = Celesto(vm_id=computer_id, **options)

    def validate_command(self, command: str, timeout: int) -> None:
        pass

    def validate_terminal(self, terminal_id: str | None) -> None:
        if terminal_id is not None:
            raise ValueError("terminal_id reattachment is only supported for cloud computers.")

    def validate_ports(self) -> NoReturn:
        raise CelestoError(
            "Published ports are unavailable on local computers; use CloudComputer() "
            "to publish an HTTP application from a cloud computer."
        )

    def run(self, command: str, timeout: int) -> CommandResult:
        runtime = self._desktop if self._desktop is not None else self._runtime
        return runtime.run(command, timeout=timeout)

    def run_stream(self, command: str, timeout: int) -> Iterator[CommandEvent]:
        if self._desktop is not None:
            # Match _ComputerSandbox.run: commands execute as the desktop user.
            command = f"runuser -u agent -- sh -lc {shlex.quote(command)}"
            return self._runtime.run_stream(command, timeout=timeout, shell="raw")
        return self._runtime.run_stream(command, timeout=timeout)

    def terminal(self, *, terminal_id: str | None) -> TerminalConnection:
        return local_terminal_connection(self._runtime.attach_shell)

    def browser(self) -> BrowserConnection:
        from celesto._connections import local_connection

        result = local_connection(self._runtime, "browser", self._connection_forwards)
        assert isinstance(result, BrowserConnection)
        return result

    def display(self, *, mode: DisplayMode) -> DisplayConnection:
        from celesto._connections import local_connection

        result = local_connection(self._runtime, mode, self._connection_forwards)
        assert isinstance(result, DisplayConnection)
        return result

    def publish_port(self, port: int) -> PublishedPort:
        self.validate_ports()

    def published_ports(self) -> list[PublishedPort]:
        self.validate_ports()

    def unpublish_port(self, port: int) -> PublishedPort:
        self.validate_ports()

    def delete(self) -> None:
        runtime = self._desktop if self._desktop is not None else self._vm
        if runtime is not None:
            runtime.delete()

    def close(self) -> None:
        if self._vm is not None:
            self._vm._cleanup_local_forwards()
            self._connection_forwards.clear()
        runtime = self._desktop if self._desktop is not None else self._vm
        if runtime is not None:
            runtime.close()
