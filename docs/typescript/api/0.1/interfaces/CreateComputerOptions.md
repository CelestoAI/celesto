[**@celestoai/celesto**](../README.md)

______________________________________________________________________

[@celestoai/celesto](../README.md) / CreateComputerOptions

# Interface: CreateComputerOptions

Start a complete Linux desktop with a display, Chromium, files, and commands.

## Properties

### backend?

> `optional` **backend?**: `"firecracker"` | `"qemu"` | `"auto"`

______________________________________________________________________

### display?

> `optional` **display?**: `object`

#### height

> **height**: `number`

#### width

> **width**: `number`

______________________________________________________________________

### name?

> `optional` **name?**: `string`

______________________________________________________________________

### network?

> `optional` **network?**: [`NetworkPolicy`](../type-aliases/NetworkPolicy.md)

______________________________________________________________________

### resources?

> `optional` **resources?**: `object`

#### diskMiB?

> `optional` **diskMiB?**: `number`

#### memoryMiB?

> `optional` **memoryMiB?**: `number`

#### vcpus?

> `optional` **vcpus?**: `2`

______________________________________________________________________

### template?

> `optional` **template?**: `"linux-desktop"`

______________________________________________________________________

### workspace?

> `optional` **workspace?**: readonly `object`\[\]
