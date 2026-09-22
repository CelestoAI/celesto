[**@celestoai/celesto**](../README.md)

______________________________________________________________________

[@celestoai/celesto](../README.md) / BrowserSessionClient

# Interface: BrowserSessionClient

Control a ready browser computer through private automation and viewing addresses. An endpoint is a local address used to connect to that computer.

## Extends

- [`CommandFilesClient`](CommandFilesClient.md)

## Properties

### cdpUrl

> `readonly` **cdpUrl**: `string`

______________________________________________________________________

### displayUrl?

> `readonly` `optional` **displayUrl?**: `string`

______________________________________________________________________

### files

> `readonly` **files**: [`SandboxFiles`](SandboxFiles.md)

#### Inherited from

[`CommandFilesClient`](CommandFilesClient.md).[`files`](CommandFilesClient.md#files)

______________________________________________________________________

### profileId?

> `readonly` `optional` **profileId?**: `string`

______________________________________________________________________

### sandboxId

> `readonly` **sandboxId**: `string`

______________________________________________________________________

### sessionId

> `readonly` **sessionId**: `string`

______________________________________________________________________

### status

> `readonly` **status**: [`BrowserSessionStatus`](../type-aliases/BrowserSessionStatus.md)

______________________________________________________________________

### viewerUrl?

> `readonly` `optional` **viewerUrl?**: `string`

## Methods

### delete()

> **delete**(): `Promise`\<`void`>

#### Returns

`Promise`\<`void`>

______________________________________________________________________

### exec()

> **exec**(`command`, `options?`): `Promise`\<[`ExecResult`](ExecResult.md)>

#### Parameters

##### command

`string` | readonly `string`\[\]

##### options?

[`ExecOptions`](ExecOptions.md)

#### Returns

`Promise`\<[`ExecResult`](ExecResult.md)>

#### Inherited from

[`CommandFilesClient`](CommandFilesClient.md).[`exec`](CommandFilesClient.md#exec)
