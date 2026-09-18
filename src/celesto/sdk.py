"""A shared lifecycle for local and cloud computers."""

from __future__ import annotations

import inspect
from contextlib import suppress
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any, Literal

from celesto.exceptions import CelestoError, VMNotFoundError
from celesto.facade import Celesto
from celesto.types import CommandResult

if TYPE_CHECKING:
    from celesto._cloud import _CloudComputer


class Computer:
    """A cloud or local computer with explicit ownership and deferred creation.

    Pass ``local=True`` to run on this machine. Ephemeral computers are deleted on
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
        if not isinstance(local, bool):
            raise ValueError("local must be True or False.")
        if lifetime not in ("ephemeral", "persistent"):
            raise ValueError("lifetime must be 'ephemeral' or 'persistent'.")
        if "vm_id" in options or "state_manager" in options:
            raise ValueError("Use Computer.get(id, local=True) to reconnect to a computer.")
        # Catch misspelled options without preparing images or allocating a VM.
        self._local = local
        if local:
            inspect.signature(Celesto).bind(**options)
            self._cloud = None
        else:
            from celesto._cloud import _CloudComputer

            self._cloud = _CloudComputer(**options)
        self._options = options.copy()
        self._lifetime = lifetime
        self._vm: Celesto | _CloudComputer | None = None
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

    def _ensure_started(self) -> Celesto | _CloudComputer:
        if self._deleted:
            raise CelestoError("This computer was deleted; create a new Computer.")
        if self._failed:
            raise CelestoError(
                f"Computer '{self.id}' failed to start; retry delete() before creating another."
            )
        if self._vm is None:
            self._vm = Celesto(**self._runtime_options()) if self._local else self._cloud
            assert self._vm is not None
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
        cls,
        computer_id: str,
        *,
        local: bool = False,
        data_dir: Path | None = None,
        **options: Any,
    ) -> Computer:
        """Attach to an existing computer without creating or starting it.

        Attached handles are persistent and cannot be used as contexts: attaching
        never implicitly takes ownership of another scope's cleanup.
        """
        if not computer_id:
            raise ValueError("computer_id must not be empty.")
        if not isinstance(computer_id, str) or not computer_id.strip():
            raise ValueError("computer_id must be a nonempty string.")
        if not isinstance(local, bool):
            raise ValueError("local must be True or False.")
        if local:
            instance = cls(local=True, lifetime="persistent", data_dir=data_dir, **options)
            instance._vm = Celesto(vm_id=computer_id, **instance._runtime_options())
        else:
            if data_dir is not None:
                raise ValueError("data_dir is only supported with local=True.")
            instance = cls(lifetime="persistent", **options)
            assert instance._cloud is not None
            instance._cloud.attach(computer_id)
            instance._vm = instance._cloud
        return instance

    def run(self, command: str, timeout: int = 30) -> CommandResult:
        """Run a shell command; nonzero exit codes are returned, not raised."""
        if not isinstance(command, str) or not command.strip():
            raise ValueError("command must be a nonempty string.")
        if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
            raise ValueError("timeout must be a positive number of seconds.")
        if self._cloud is not None:
            self._cloud.validate_command(command, timeout)
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
