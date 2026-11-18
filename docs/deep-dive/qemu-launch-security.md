# Optional QEMU launch controls

Celesto can use additional launch controls when a Linux pool operator has prepared the matching system policies and resource limits. Ordinary SDK users do not need a pool helper, extra privileges, or a different setup. These controls stay off unless the operator explicitly supplies the private launch options.

## Existing SDK behavior

Normal constructors, QEMU networking, start/stop/delete, snapshots, and detached computers keep their existing behavior. The existing `_qemu_apparmor_profile` option still selects one prepared AppArmor policy, which limits the files and operations QEMU can access. Service environment variables alone do not turn on these options for a standalone SDK caller.

The extra options are an internal integration contract for a prepared Linux pool. They are not public configuration for customer workloads and must not be copied into guest code.

## Prepared pool contract

| Option | Required preparation | Behavior |
| --- | --- | --- |
| `_qemu_per_vm_confinement=True` | Existing AppArmor profile prefix and an already owned TAP network interface | Selects a policy named with the computer ID and passes only its opened network descriptor to QEMU. |
| `_qemu_cgroup_root=Path(...)` | Root-owned per-computer resource groups and `/usr/local/sbin/celesto-pool-vm-helper` | Runs a small launcher that asks the trusted helper to join the assigned group before executing QEMU. |
| `_qemu_deadline_epoch=...` | The resource-group option and an operator-owned absolute expiry | Refuses execution after that deadline, including after helper work. The external pool must also enforce expiry for an already running computer. |
| `_qemu_log_limit_bytes=...` | At least 8 MiB of retention | Starts a detached console writer that keeps the initial 4 MiB used for SSH identity and a bounded recent tail. When a resource group is configured, the writer joins the same group. |

The SDK does not install the helper, grant sudo access, create policies or resource groups, or activate host-wide isolation. Missing preparation causes an opted-in launch to fail. Installed helper behavior, AppArmor enforcement, resource limits, network policy, and deadline enforcement require separate integration qualification.

The launcher keeps the tracked process ID across execution. It closes unrelated descriptors and uses the existing clean environment when an AppArmor policy is selected. The trusted helper receives only the computer identity, launcher PID, and process start time; the SDK does not request permission to write shared resource-group ancestors.

## Console ownership and cleanup

Each bounded-console boot publishes a fresh private log inode, so output from an older detached writer cannot overwrite a later boot. Root preserves the validated owner's user and group IDs before publishing the file. A failed ownership transfer keeps the original file and its contents. An ordinary owner retains the normal group of the fresh file, including when the old file's group is no longer assignable.

For computers that remain running under the existing manager-close contract, the console writer also stays alive. Exited writers are reaped, and live writers transfer their wait responsibility without retaining the manager. Stopping a computer waits for its writer before releasing the log. These changes do not alter the existing asynchronous-start cancellation ownership contract.

## Verification and limits

The [QEMU manager tests](../../tests/vm/test_vm_qemu.py) cover existing networking/AppArmor launches and the opted-in descriptor and environment contract. The [launcher tests](../../tests/runtime/test_qemu_launch_shim.py) cover helper refusal, deadlines, process identity, and assigned group membership.

The console [startup](../../tests/runtime/test_qemu_console_startup.py), [relay](../../tests/runtime/test_qemu_console_relay.py), [identity](../../tests/runtime/test_qemu_console_identity.py), [diagnostics](../../tests/runtime/test_qemu_console_diagnostics.py), and [cleanup](../../tests/runtime/test_qemu_console_cleanup.py) tests exercise actual child processes and produce repeatable receipts. Root-only file-ownership cases need an isolated test container; they must not change host users or request interactive sudo.

These local tests do not establish deployed helper compatibility, hardware isolation, or production readiness. The security integration can remain unactivated while the SDK continues to serve ordinary local and cloud workflows.
