# Networking

Celesto can share a service running inside a computer with your machine and control which network destinations a computer can reach.

## Share a service from a computer

If a service listens on port 3000 in computer `demo`, share it with your machine:

```bash
celesto computer port expose demo 3000
```

Use the returned port on your machine in your browser or tool. `celesto computer port list demo` shows active mappings. In `celesto computer port close demo HOST_PORT:3000`, replace `HOST_PORT` with the returned port—for example, `celesto computer port close demo 49152:3000`.

## Connect a computer directly to an existing network

On Linux, a computer can appear as a separate device on a network you already configured. This advanced mode gives the computer its own network identity instead of placing it behind Celesto's private network.

Your machine must already have a Linux bridge, a network interface that joins several connections into one network. It must be connected to the target network, and neither the bridge nor its member interfaces may have IP addresses on your machine, including automatic IPv6 addresses. Celesto checks this setup but never creates, reconfigures, or deletes the bridge.

Check bridge `br10` before creating a computer:

```bash
celesto bridge check br10
# Bridge 'br10' is ready for bridged networking.
```

Create a bridged computer only after that check passes:

```bash
celesto computer create --name demo --os alpine --network bridge --bridge br10
```

The current Celesto Alpine image automatically asks the network for an address using DHCP (Dynamic Host Configuration Protocol). To use a static address instead, add an executable `/etc/celesto/network.sh` script inside the computer's disk. Celesto passes `eth0` as the script's first argument each time the computer boots. You can open a shell in the computer before it has an address because `celesto computer shell demo` uses a direct control channel from your machine rather than the network.

Custom images must understand the `celesto.network=guest` boot setting and configure `eth0`. When creating `VMConfig` directly for a compatible image, set `guest_managed_networking=True`. Celesto rejects older published or custom images instead of starting them without working bridge configuration.

Bridge mode deliberately does not provide Celesto NAT, port exposure, SSH from your machine, shared folders, or outbound-domain controls. Connect to services inside the computer from the bridged network, and use `celesto computer shell demo` to administer it from your machine.

A bridged computer can send traffic directly to the selected network. Configuration mistakes or untrusted software inside the computer can affect other devices through duplicate addresses, address spoofing, or unwanted services. Use this mode only on a network where that access is acceptable.

## Turn outbound access off

Computers that use QEMU on macOS and Linux can keep local applications and shared folders usable while blocking outbound access. Open access remains the default; opt in with `mode="off"`:

```python
from celesto import Celesto

with Celesto(backend="qemu", internet_settings={"mode": "off"}) as computer:
    print(computer.run("echo hello").stdout)
```

The default QEMU network, called **slirp**, needs no administrator setup. Off mode uses QEMU's built-in restriction and disables IPv6. It blocks external TCP, UDP, and DNS, including QEMU's virtual DNS service. Port forwarding you set up explicitly remains available: turning outbound access off does not prevent your machine from connecting to an application inside the computer.

Shared folders keep their existing setup requirements: a compatible image and a working SSH connection for folder setup. No new command connection is needed for ordinary application traffic.

### Firecracker

On Linux, for computers that use Firecracker, turn outbound networking off while keeping commands and file transfers available:

```python
from celesto import Celesto

with Celesto(
    backend="firecracker",
    comm_channel="vsock",
    internet_settings={"mode": "off"},
) as computer:
    print(computer.run("echo hello").stdout)
```

The `vsock` setting uses a direct connection to the computer for commands and files. It does not need internet access. Networking off blocks IP traffic started inside the computer, including DNS and connections to your machine. Command output and explicit file downloads can still leave the computer through this direct connection.

The default mode is `open`, which enables internet access. Managed Linux TAP networking blocks connections between computers and to IPv4 link-local addresses, including the common cloud metadata address `169.254.169.254`. It does not block every private network or every cloud provider's metadata service. These TAP isolation rules are not a claim about default-open slirp networking.

After upgrading, existing running computers keep their current network rules until Celesto repairs their networking or they restart. Restart them to apply the updated baseline isolation. To use `off` or `restricted`, create a new computer with those settings; reconnecting does not change an existing computer's policy.

## Allow specific IP addresses

Use `restricted` with the IPv4 addresses or network ranges your task needs:

Replace `203.0.113.10` below with your service's actual address:

```python
from celesto import Celesto

with Celesto(
    backend="firecracker",
    comm_channel="vsock",
    internet_settings={
        "mode": "restricted",
        "allowed_cidrs": ["203.0.113.10/32"],
    },
) as computer:
    print(computer.run("echo hello").stdout)
```

`/32` means one address; a range such as `10.20.0.0/24` includes multiple addresses. Bare IPv4 addresses are also accepted.

Only the listed destinations can receive new outbound connections, on any port or protocol. IPv6 and connections from the computer to your machine are blocked. QEMU can still reply to your machine's TCP connections, as described below. The address range Celesto uses for computers and link-local address ranges cannot be allowed. There is no automatic DNS exception: use an IP address directly or explicitly include the resolver's address. Allowing a resolver permits other traffic to that same address too.

Firecracker requires the direct `vsock` control connection for these modes; its shared folders and exposed ports remain unsupported. QEMU supports the combinations below. Unsupported combinations fail before image preparation or resource allocation. Policy survives restart and supported snapshot restore; create a new computer to change it.

### QEMU address restrictions on Linux

Use **TAP networking** when a computer that uses QEMU on Linux needs a list of allowed addresses. TAP gives the computer its own private IP and uses Linux firewall rules; it requires the existing Celesto Linux networking setup and privileges. Celesto never switches to TAP automatically.

With a previously prepared `BootImage` named `image`, create the computer explicitly:

```python
computer = Celesto.from_image(
    image,
    backend="qemu",
    network="tap",
    internet_settings={"mode": "restricted", "allowed_cidrs": ["203.0.113.10/32"]},
)
```

Replace the example address with your application's destination. For direct `VMConfig` construction, set `backend="qemu"`, `qemu_network="tap"`, and the same `internet_settings`. Use `mode="off"` with TAP to allow no outbound destinations.

| QEMU network | macOS | Linux | Local application access |
| --- | --- | --- | --- |
| Default slirp | Open, off | Open, off | `port_forwards` or `expose_local()` |
| Explicit TAP | Unsupported | Open, off, restricted IPv4 addresses | The computer's IP or `expose_local()` |

These controls apply to computers running Linux. Windows and macOS computers are not included.

In off/restricted TAP modes, the computer can reply to IPv4 TCP connections initiated by your machine. This keeps applications, SSH, and shared-folder setup usable without allowing new outbound connections to your machine. The exception does not allow traffic started inside the computer, IPv6, or forwarding between computers.

### Access a QEMU application

Have your application listen on `0.0.0.0` inside the computer, then expose its port after starting it:

```python
computer.start()
port = computer.expose_local(8080)
print(f"http://127.0.0.1:{port}")
```

HTTP, WebSockets, and application file transfers use QEMU forwarding on slirp or localhost firewall forwarding on TAP. They do not require SSH or a guest agent. An application bound only to the computer's `127.0.0.1` still needs the existing SSH-based `guest_loopback=True` option.

Slirp preserves configured launch-time `port_forwards` through restart and snapshot restore. TAP does not support that setting; use the computer's IP or `expose_local()` instead. Dynamic exposures retain their existing lifetime: recreate them after pause, stop, or restore.

`Celesto.from_image(..., state_manager=inventory)` and `Celesto.from_snapshot(..., state_manager=inventory)` can share the same inventory, just like direct construction. The existing QEMU snapshot requirements still apply: an isolated qcow2 disk and no shared folders. See [snapshots](snapshots.md). A disk imported as a new image receives the policy of its new computer's configuration; it does not carry policy by itself.

On the tested QEMU 11.0.0/macOS HVF setup, use disk snapshots: full-memory restore hits a QEMU assertion that also reproduces on v0.0.32. See the [validation notes](../deep-dive/qemu-network-policy-validation.md#evidence-status).

These controls intentionally do not add dynamic domain rules, DNS services, proxies, helper computers, or per-command policy checks. Policy work happens during network setup and lifecycle reconciliation. Production rollout requires the separate [QEMU validation gates](../deep-dive/qemu-network-policy-validation.md).

## Legacy domain lists

Existing callers can continue to use domain lists on supported private networking:

```python
with Celesto(internet_settings={"allowed_domains": ["api.example.com"]}) as computer:
    computer.run("curl https://api.example.com")
```

Celesto resolves the names to IPv4 addresses during setup and allows traffic to those addresses on any port. It does not verify the hostname on each connection. Shared hosting may permit other services at the same address, and changing DNS answers may prevent an allowed service from working. DNS servers are not automatically allowed.

Use `"*"` to allow all destinations. Entries may be hostnames or URLs without a path; Celesto stores their hostnames. Do not combine domain lists with the new modes. HTTP-method restrictions are unsupported and rejected.

Legacy domain lists require Firecracker private networking or QEMU with `VMConfig.qemu_network="tap"`. Other networking configurations reject restrictions instead of continuing without enforcement. These lists are a compatibility feature, not strict domain filtering.

## Validate settings and handle errors

Use the exported settings class for editor suggestions. Lists are accepted as input; stored collections are immutable tuples. Saved JSON still uses arrays, including when loading older settings. Create a new computer to change its policy.

```python
from celesto import InternetSettings

policy = InternetSettings(mode="restricted", allowed_cidrs=["203.0.113.10"])
```

Unknown fields are errors: misspelling `mode` cannot silently enable internet access, and unsupported options such as `allowed_ports` are rejected. Invalid settings fail before image preparation.

Public SDK operations raise `celesto.ValidationError` for invalid or unsupported policy settings. It is also a `CelestoError`. For invalid fields, `details["errors"]` contains the field locations, messages, and input values:

```python
from celesto import Celesto, ValidationError

try:
    Celesto(internet_settings={"mode": "restricted"})
except ValidationError as error:
    print(error)  # restricted requires allowed_cidrs
    print(error.details.get("errors", []))
```

Constructing `InternetSettings(...)` or `VMConfig(...)` directly uses Pydantic's `ValidationError`. This is separate from the SDK operation error above.

Python reconnect and snapshot restore must share an inventory. See the [Python snapshot example](snapshots.md#save-and-restore-from-python); setting the same `data_dir` alone does not share inventory.
