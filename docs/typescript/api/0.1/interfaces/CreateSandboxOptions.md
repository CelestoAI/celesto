[**@celestoai/celesto**](../README.md)

______________________________________________________________________

[@celestoai/celesto](../README.md) / CreateSandboxOptions

# Interface: CreateSandboxOptions

Configure the operating system, resources, image, and network for a new sandbox. MiB means mebibytes, a memory and disk-size unit.

## Properties

### backend?

> `optional` **backend?**: `"firecracker"` | `"qemu"` | `"libkrun"` | `"vz"`

Override automatic backend selection.

______________________________________________________________________

### diskMiB?

> `optional` **diskMiB?**: `number`

Guest root disk size in MiB.

______________________________________________________________________

### image?

> `optional` **image?**: `string`

Custom local path, file URL, or remote image reference.

______________________________________________________________________

### memoryMiB?

> `optional` **memoryMiB?**: `number`

Guest memory in MiB.

______________________________________________________________________

### network?

> `optional` **network?**: [`NetworkPolicy`](../type-aliases/NetworkPolicy.md)

Outbound network access. Defaults to open.

______________________________________________________________________

### os?

> `optional` **os?**: `"ubuntu"` | `"alpine"`

Guest operating system. Defaults to Ubuntu.
