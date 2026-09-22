[**@celestoai/celesto**](../README.md)

______________________________________________________________________

[@celestoai/celesto](../README.md) / SandboxFiles

# Interface: SandboxFiles

Read, write, upload, and download files for one sandbox.

## Methods

### download()

> **download**(`sandboxPath`, `localPath`): `Promise`\<`void`>

Download to a temporary host file, then rename it atomically.

#### Parameters

##### sandboxPath

`string`

##### localPath

`string`

#### Returns

`Promise`\<`void`>

______________________________________________________________________

### read()

> **read**(`path`): `Promise`\<`string`>

Read a UTF-8 text file from an absolute sandbox path.

#### Parameters

##### path

`string`

#### Returns

`Promise`\<`string`>

______________________________________________________________________

### upload()

> **upload**(`localPath`, `sandboxPath`): `Promise`\<`void`>

Stream a host file when the transport supports it; otherwise buffer the complete file before writing it.

#### Parameters

##### localPath

`string`

##### sandboxPath

`string`

#### Returns

`Promise`\<`void`>

______________________________________________________________________

### write()

> **write**(`path`, `content`): `Promise`\<`void`>

Write text or bytes to an absolute sandbox path.

#### Parameters

##### path

`string`

##### content

`string` | `Uint8Array`\<`ArrayBufferLike`>

#### Returns

`Promise`\<`void`>
