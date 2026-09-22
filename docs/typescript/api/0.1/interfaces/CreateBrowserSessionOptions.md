[**@celestoai/celesto**](../README.md)

______________________________________________________________________

[@celestoai/celesto](../README.md) / CreateBrowserSessionOptions

# Interface: CreateBrowserSessionOptions

Start an isolated browser computer with the resources and live view you need. Chromium is the browser engine running inside it.

## Properties

### allowDownloads?

> `optional` **allowDownloads?**: `boolean`

______________________________________________________________________

### backend?

> `optional` **backend?**: `"firecracker"` | `"qemu"` | `"libkrun"` | `"auto"`

______________________________________________________________________

### diskMiB?

> `optional` **diskMiB?**: `number`

______________________________________________________________________

### memoryMiB?

> `optional` **memoryMiB?**: `number`

______________________________________________________________________

### mode?

> `optional` **mode?**: `"headless"` | `"live"`

______________________________________________________________________

### network?

> `optional` **network?**: [`NetworkPolicy`](../type-aliases/NetworkPolicy.md)

______________________________________________________________________

### profile?

> `optional` **profile?**: { `mode`: `"ephemeral"`; } | { `id`: `string`; `mode`: `"persistent"`; }

______________________________________________________________________

### recordVideo?

> `optional` **recordVideo?**: `boolean`

______________________________________________________________________

### sessionId?

> `optional` **sessionId?**: `string`

______________________________________________________________________

### timeoutMinutes?

> `optional` **timeoutMinutes?**: `number`

______________________________________________________________________

### viewport?

> `optional` **viewport?**: `object`

#### height

> **height**: `number`

#### width

> **width**: `number`
