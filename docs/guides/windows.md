# Windows computers

Celesto can run a Windows computer from a Windows disk image that you build yourself. This is useful for Windows-only software; it is a specialized QEMU workflow rather than the default way to create a computer.

## Build an image

Get a Windows ISO and a virtio driver ISO, then build a reusable qcow2 image. Choose a strong password instead of the development default. Set a trusted SSH key file before starting the build:

```bash
export CELESTO_SSH_KNOWN_HOSTS="$PWD/windows-known-hosts"
celesto windows build-image \
  --iso ./Win11.iso \
  --virtio-win-iso ./virtio-win.iso \
  --output ./win11.qcow2 \
  --hostname celesto-win \
  --password 'choose-a-strong-password'
```

Windows installation can take a while. The builder uses the chosen hostname (`celesto-win` above) as a stable SSH identity, so its key file does not need to predict the randomly assigned connection port. The readiness check rejects unknown or changed keys before sending the password.

Initial trust still requires a verified public server key. Windows does not publish it through Celesto's boot console, so a stock ISO build is not fully unattended until you provide that key through a trusted Windows console or image-building process. With the default [Windows OpenSSH configuration](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh-server-configuration), the public key is available from the Windows console with:

```powershell
Get-Content "$env:ProgramData\ssh\ssh_host_ed25519_key.pub"
```

Save that independently verified public key as `verified-windows-host-key.pub` on your machine. In another terminal, add it under the same hostname in the file configured above:

```bash
printf 'celesto-win %s\n' "$(cat ./verified-windows-host-key.pub)" > ./windows-known-hosts
chmod 600 ./windows-known-hosts
```

The builder rereads this file while waiting for SSH, so you can provision the key after Windows creates it during installation. Do not obtain the trusted key from the unverified SSH connection. Use a separate alias for each independently built image. The resulting `win11.qcow2` is the input for a Windows computer.

## Start a Windows computer

Use Python so you can provide the username, password, and SSH identity chosen while building the image. Keep `CELESTO_SSH_KNOWN_HOSTS` set to the same trusted key file and pass `ssh_host_key_alias` on each new `Celesto` object. The alias works across changing connection ports for Python commands and interactive SSH. See [SSH identity setup](../security.md#verify-ssh-identity).

```python
from celesto import Celesto

with Celesto(
    os="windows",
    image="./win11.qcow2",
    ssh_user="celesto",
    ssh_password="choose-a-strong-password",
    ssh_host_key_alias="celesto-win",
) as computer:
    result = computer.run("Get-ComputerInfo | Select-Object WindowsProductName")
    print(result.stdout)
```

The generic `celesto computer create` command does not currently accept Windows login credentials, so it cannot complete the readiness check for this password-based image ([CLI options](../../src/celesto/cli/commands/app.py), [image configuration](../../src/celesto/facade.py)).

Windows computers are currently supported when your machine runs Linux on x86_64, and Celesto controls them over SSH. They do not support shared folders, outbound-domain controls, or snapshots.

## Implementation notes

The image builder creates the unattended install media and waits for the installed system in [`src/celesto/windows/build_image.py`](../../src/celesto/windows/build_image.py). Windows platform settings are in [`src/celesto/runtime/guest_platforms.py`](../../src/celesto/runtime/guest_platforms.py); configuration restrictions are enforced in [`src/celesto/facade.py`](../../src/celesto/facade.py) and [`src/celesto/vm.py`](../../src/celesto/vm.py). See [`tests/windows/test_windows_build_image.py`](../../tests/windows/test_windows_build_image.py).
