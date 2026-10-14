# Windows computers

Celesto can run a Windows computer from a Windows disk image that you build yourself. This is useful for Windows-only software; it is a specialized QEMU workflow rather than the default way to create a computer.

## Build an image

Get a Windows ISO and a virtio driver ISO, then build a reusable qcow2 image. Choose a strong password instead of the development default.

```bash
celesto windows build-image \
  --iso ./Win11.iso \
  --virtio-win-iso ./virtio-win.iso \
  --output ./win11.qcow2 \
  --password 'choose-a-strong-password'
```

The build is unattended and can take a while. The resulting `win11.qcow2` is the input for a Windows computer.

## Start a Windows computer

Use Python so you can provide the username and password chosen while building the image:

```python
from celesto import Celesto

with Celesto(
    os="windows",
    image="./win11.qcow2",
    ssh_user="celesto",
    ssh_password="choose-a-strong-password",
) as computer:
    result = computer.run("Get-ComputerInfo | Select-Object WindowsProductName")
    print(result.stdout)
```

The generic `celesto computer create` command does not currently accept Windows login credentials, so it cannot complete the readiness check for this password-based image ([CLI options](../../src/celesto/cli/commands/app.py), [image configuration](../../src/celesto/facade.py)).

Windows computers are currently supported when your machine runs Linux on x86_64, and Celesto controls them over SSH. They do not support shared folders, outbound-domain controls, or snapshots.

## Implementation notes

The image builder creates the unattended install media and waits for the installed system in [`src/celesto/windows/build_image.py`](../../src/celesto/windows/build_image.py). Windows platform settings are in [`src/celesto/runtime/guest_platforms.py`](../../src/celesto/runtime/guest_platforms.py); configuration restrictions are enforced in [`src/celesto/facade.py`](../../src/celesto/facade.py) and [`src/celesto/vm.py`](../../src/celesto/vm.py). See [`tests/windows/test_windows_build_image.py`](../../tests/windows/test_windows_build_image.py).
