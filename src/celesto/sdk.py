"""Local computer lifecycle, independent of the cloud transport planned later."""

from __future__ import annotations

import inspect
from contextlib import suppress
from pathlib import Path
from types import TracebackType
from typing import Any, Literal

from celesto.exceptions import CelestoError, VMNotFoundError
from celesto.facade import Celesto
from celesto.types import CommandResult


class Computer:
    """A local computer with explicit ownership and deferred creation.

    Pass ``local=True`` in this release. Ephemeral computers are deleted on
    context exit, not on garbage collection or a hard process crash. Outside
    a context, call ``delete()`` explicitly for either lifetime.

    Local VM options (such as ``os``, ``memory``, and ``mounts``) are forwarded
    to the local runtime. Existing data directories and image caches are reused.
    """

    def __init__(
        self,
        *,
        local: bool = False,
        lifetime: Literal["ephemeral", "persistent"] = "ephemeral",
        **options: Any,
    ) -> None:
        if local is not True:
            raise ValueError("Cloud support is not available yet; use Computer(local=True).")
        if lifetime not in ("ephemeral", "persistent"):
            raise ValueError("lifetime must be 'ephemeral' or 'persistent'.")
        if "vm_id" in options or "state_manager" in options:
            raise ValueError("Use Computer.get(id, local=True) to reconnect to a computer.")
        # Catch misspelled options without preparing images or allocating a VM.
        inspect.signature(Celesto).bind(**options)
        self._options = options.copy()
        self._lifetime = lifetime
        self._vm: Celesto | None = None
        self._deleted = False
        self._entered = False
        self._failed = False

    @property
    def lifetime(self) -> Literal["ephemeral", "persistent"]:
        return self._lifetime

    @property
    def id(self) -> str | None:
        """Stable ID after creation; inspecting this never creates a computer."""
        return self._vm.vm_id if self._vm is not None else None

    def _runtime_options(self) -> dict[str, Any]:
        from celesto.cli.state import create_cli_state_manager
        from celesto.vm import resolve_data_dir

        options = self._options.copy()
        data_dir = resolve_data_dir(options.get("data_dir"))
        options["data_dir"] = data_dir
        options["state_manager"] = create_cli_state_manager(data_dir / "smolvm.db")
        return options

    def _ensure_started(self) -> Celesto:
        if self._deleted:
            raise CelestoError("This computer was deleted; create a new Computer(local=True).")
        if self._failed:
            raise CelestoError(
                f"Computer '{self.id}' failed to start; run "
                f"'celesto sandbox delete {self.id}' or retry delete() before creating another."
            )
        if self._vm is None:
            self._vm = Celesto(**self._runtime_options())
            try:
                self._vm.start()
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
        return self._vm

    @classmethod
    def get(
        cls, computer_id: str, *, local: bool = False, data_dir: Path | None = None
    ) -> Computer:
        """Attach to an existing local computer without creating or starting it.

        Attached handles are persistent and cannot be used as contexts: attaching
        never implicitly takes ownership of another scope's cleanup.
        """
        if not computer_id:
            raise ValueError("computer_id must not be empty.")
        instance = cls(local=local, lifetime="persistent", data_dir=data_dir)
        instance._vm = Celesto(vm_id=computer_id, **instance._runtime_options())
        return instance

    def run(self, command: str, timeout: int = 30) -> CommandResult:
        """Run a shell command; nonzero exit codes are returned, not raised."""
        if not isinstance(command, str) or not command.strip():
            raise ValueError("command must be a nonempty string.")
        if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
            raise ValueError("timeout must be a positive number of seconds.")
        return self._ensure_started().run(command, timeout=timeout)

    def delete(self) -> None:
        """Delete this computer; failed cleanup can be retried on the same handle."""
        if self._deleted:
            return
        if self._vm is not None:
            with suppress(VMNotFoundError):
                self._vm.delete()
            self._vm.close()
        self._deleted = True

    def __enter__(self) -> Computer:
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
