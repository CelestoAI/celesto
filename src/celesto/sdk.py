"""A shared lifecycle for local and cloud computers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path
from threading import Lock
from types import TracebackType
from typing import Any, ClassVar, Literal, Self, Unpack

from celesto._connection_info import DisplayMode, validate_display_mode
from celesto._providers import ProviderName, make_provider, resolve_provider
from celesto._providers.base import ComputerProvider
from celesto._providers.cloud import CloudProvider
from celesto._providers.options import CloudOptions, LocalOptions
from celesto._telemetry import observe_sdk_operation
from celesto._terminal import TerminalConnection, validate_terminal_id
from celesto.exceptions import CelestoError, VMNotFoundError
from celesto.types import (
    BrowserConnection,
    CommandEvent,
    CommandResult,
    DisplayConnection,
    PublishedPort,
)


class Computer:
    """A cloud or local computer with explicit ownership and deferred creation.

    Runs locally by default; pass ``provider="cloud"`` for cloud execution.
    Ephemeral computers are deleted on context exit, not on garbage collection
    or a hard process crash. Outside
    a context, call ``delete()`` explicitly for either lifetime.

    Local VM options (such as ``os``, ``memory``, and ``mounts``) are forwarded
    to the local runtime. Existing data directories and image caches are reused.
    """

    _fixed_provider: ClassVar[ProviderName | None] = None

    def __init__(
        self,
        *,
        provider: ProviderName | None = None,
        local: bool | None = None,
        lifetime: Literal["ephemeral", "persistent"] = "ephemeral",
        **options: Any,
    ) -> None:
        selected = resolve_provider(provider, local, self._fixed_provider)
        if lifetime not in ("ephemeral", "persistent"):
            raise ValueError("lifetime must be 'ephemeral' or 'persistent'.")
        if "vm_id" in options or "state_manager" in options:
            raise ValueError(
                f"Use Computer.get(id, provider='{selected}') to reconnect to a computer."
            )
        self._provider_name = selected
        self._provider = make_provider(selected, options)
        self._connection_lock = Lock()
        self._lifetime = lifetime
        self._started = False
        self._deleted = False
        self._entered = False
        self._failed = False

    @property
    def lifetime(self) -> Literal["ephemeral", "persistent"]:
        return self._lifetime

    @property
    def id(self) -> str | None:
        """Stable ID after creation; inspecting this never creates a computer."""
        return self._provider.id

    @property
    def provider(self) -> ProviderName:
        """Execution location, fixed for the lifetime of this handle."""
        return self._provider_name

    def _ensure_started(self) -> ComputerProvider:
        if self._deleted:
            raise CelestoError("This computer was deleted; create a new Computer.")
        if self._failed:
            raise CelestoError(
                f"Computer '{self.id}' failed to start; retry delete() before creating another."
            )
        if not self._started:
            try:
                self._provider.start()
                self._started = True
            except BaseException as startup_error:
                self._failed = True
                try:
                    self.delete()
                except BaseException as cleanup_error:
                    raise BaseExceptionGroup(
                        f"Computer '{self.id}' failed to start and could not be deleted",
                        [startup_error, cleanup_error],
                    ) from None
                raise
        return self._provider

    @classmethod
    def get(
        cls,
        computer_id: str,
        *,
        provider: ProviderName | None = None,
        local: bool | None = None,
        data_dir: Path | None = None,
        **options: Any,
    ) -> Self:
        """Attach to an existing computer without creating or starting it.

        Attached handles are persistent and cannot be used as contexts: attaching
        never implicitly takes ownership of another scope's cleanup.
        """
        if not computer_id:
            raise ValueError("computer_id must not be empty.")
        if not isinstance(computer_id, str) or not computer_id.strip():
            raise ValueError("computer_id must be a nonempty string.")
        selected = resolve_provider(provider, local, cls._fixed_provider)
        if data_dir is not None:
            if selected != "local":
                raise ValueError("data_dir is only supported with provider='local'.")
            options["data_dir"] = data_dir
        instance = cls(provider=selected, lifetime="persistent", **options)
        try:
            instance._provider.attach(computer_id)
        except BaseException:
            instance._provider.close()
            raise
        instance._started = True
        return instance

    @observe_sdk_operation("command_execution")
    def run(self, command: str, timeout: int = 30) -> CommandResult:
        """Run a shell command; nonzero exit codes are returned, not raised."""
        self._validate_run(command, timeout)
        self._provider.validate_command(command, timeout)
        return self._ensure_started().run(command, timeout=timeout)

    def run_stream(self, command: str, timeout: int = 30) -> Iterator[CommandEvent]:
        """Yield started, stdout, stderr, and exit events as a command runs."""
        self._validate_run(command, timeout)
        self._provider.validate_command(command, timeout)
        runtime = self._ensure_started()
        return runtime.run_stream(command, timeout=timeout)

    def terminal(self, *, terminal_id: str | None = None) -> TerminalConnection:
        """Create an interactive terminal connection.

        Call ``attach()`` on the returned connection to bridge this process's
        stdin and stdout. Cloud terminal IDs can be supplied later to reattach.
        Local terminal sessions don't support reattachment.
        """
        validate_terminal_id(terminal_id)
        self._provider.validate_terminal(terminal_id)
        runtime = self._ensure_started()
        return runtime.terminal(terminal_id=terminal_id)

    @staticmethod
    def _validate_run(command: str, timeout: int) -> None:
        if not isinstance(command, str) or not command.strip():
            raise ValueError("command must be a nonempty string.")
        if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
            raise ValueError("timeout must be a positive number of seconds.")

    @observe_sdk_operation("browser")
    def browser(self) -> BrowserConnection:
        """Return a CDP WebSocket URL for Playwright; request again to refresh it."""
        with self._connection_lock:
            return self._ensure_started().browser()

    @observe_sdk_operation("desktop")
    def display(self, *, mode: DisplayMode = "read_only") -> DisplayConnection:
        """Return a VNC-over-WebSocket URL for noVNC, not an HTML viewer page."""
        validate_display_mode(mode)
        with self._connection_lock:
            return self._ensure_started().display(mode=mode)

    def _port_provider(self) -> ComputerProvider:
        self._provider.validate_ports()
        return self._ensure_started()

    @staticmethod
    def _validate_port(port: int) -> None:
        if isinstance(port, bool) or not isinstance(port, int) or not 1024 <= port <= 65535:
            raise ValueError("port must be an integer from 1024 to 65535.")

    def publish_port(self, port: int) -> PublishedPort:
        """Publish an HTTP application to the internet (cloud only).

        Creates this computer if needed. The application must already be listening
        on the port. The service may reject reserved ports within the allowed range.
        Requests are never automatically replayed after a transport failure.
        """
        self._validate_port(port)
        return self._port_provider().publish_port(port)

    def published_ports(self) -> list[PublishedPort]:
        """Fetch active public routes (cloud only), creating this computer if needed."""
        return self._port_provider().published_ports()

    def unpublish_port(self, port: int) -> PublishedPort:
        """Remove a public route without stopping its application (cloud only).

        Creates this computer if needed. Removing an absent route is safe, but
        requests are never automatically replayed after a transport failure.
        """
        self._validate_port(port)
        return self._port_provider().unpublish_port(port)

    def close(self) -> None:
        """Release this handle's resources without stopping or deleting the computer.

        Local forwards owned by this handle are removed. Other handles and the
        running desktop are unaffected. Use ``Computer.get(id)`` to reconnect.
        """
        with self._connection_lock:
            self._provider.close()

    def delete(self) -> None:
        """Delete this computer; failed cleanup can be retried on the same handle."""
        if self._deleted:
            return
        with suppress(VMNotFoundError):
            self._provider.delete()
        self._provider.close()
        self._deleted = True

    @observe_sdk_operation("computer")
    def start(self) -> Self:
        """Create and start this computer if it has not been created yet."""
        self._ensure_started()
        return self

    def stop(self) -> Self:
        """Stop a cloud computer while retaining its files for a later resume."""
        if self._provider_name != "cloud":
            raise CelestoError("Stopping a local computer is not supported by this API.")
        if self._deleted or not self._started:
            raise CelestoError("This computer is not running; create or reconnect to it first.")
        assert isinstance(self._provider, CloudProvider)
        self._provider.stop()
        return self

    def resume(self) -> Self:
        """Start a previously stopped cloud computer without creating a new one."""
        if self._provider_name != "cloud":
            raise CelestoError("Resuming a local computer is not supported by this API.")
        if self._deleted or not self._started:
            raise CelestoError(
                "This computer has not been created; create or reconnect to it first."
            )
        assert isinstance(self._provider, CloudProvider)
        self._provider.resume()
        return self

    def __enter__(self) -> Self:
        if self.lifetime == "persistent":
            raise ValueError(
                "Persistent computers cannot use 'with'; use an ephemeral Computer "
                "or call delete() explicitly."
            )
        if self._entered:
            raise ValueError("This computer already has an active 'with' block.")
        self._ensure_started()
        self._entered = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            self.delete()
        except BaseException as cleanup_error:
            if exc is not None:
                raise BaseExceptionGroup(
                    f"Computer '{self.id}' body and cleanup both failed", [exc, cleanup_error]
                ) from None
            raise
        finally:
            self._entered = False


class LocalComputer(Computer):
    """A computer on this machine, with the shared Computer API."""

    _fixed_provider: ClassVar[ProviderName | None] = "local"

    def __init__(
        self,
        *,
        provider: ProviderName | None = None,
        local: bool | None = None,
        lifetime: Literal["ephemeral", "persistent"] = "ephemeral",
        **options: Unpack[LocalOptions],
    ) -> None:
        super().__init__(provider=provider, local=local, lifetime=lifetime, **options)


class CloudComputer(Computer):
    """A computer in Celesto Cloud, with the shared Computer API."""

    _fixed_provider: ClassVar[ProviderName | None] = "cloud"

    def __init__(
        self,
        *,
        provider: ProviderName | None = None,
        local: bool | None = None,
        lifetime: Literal["ephemeral", "persistent"] = "ephemeral",
        **options: Unpack[CloudOptions],
    ) -> None:
        super().__init__(provider=provider, local=local, lifetime=lifetime, **options)
