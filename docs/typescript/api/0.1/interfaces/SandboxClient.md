[**@celestoai/celesto**](../README.md)

***

[@celestoai/celesto](../README.md) / SandboxClient

# Interface: SandboxClient

The mockable command, file, status, and deletion contract for one sandbox.

## Extends

- [`CommandFilesClient`](CommandFilesClient.md)

## Properties

### files

> `readonly` **files**: [`SandboxFiles`](SandboxFiles.md)

#### Inherited from

[`CommandFilesClient`](CommandFilesClient.md).[`files`](CommandFilesClient.md#files)

***

### id

> `readonly` **id**: `string`

***

### status

> `readonly` **status**: [`SandboxStatus`](../type-aliases/SandboxStatus.md)

## Methods

### delete()

> **delete**(): `Promise`\<`void`\>

#### Returns

`Promise`\<`void`\>

***

### exec()

> **exec**(`command`, `options?`): `Promise`\<[`ExecResult`](ExecResult.md)\>

#### Parameters

##### command

`string` \| readonly `string`[]

##### options?

[`ExecOptions`](ExecOptions.md)

#### Returns

`Promise`\<[`ExecResult`](ExecResult.md)\>

#### Inherited from

[`CommandFilesClient`](CommandFilesClient.md).[`exec`](CommandFilesClient.md#exec)
