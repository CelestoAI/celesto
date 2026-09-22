[**@celestoai/celesto**](../README.md)

______________________________________________________________________

[@celestoai/celesto](../README.md) / ComputerSessionClient

# Interface: ComputerSessionClient

A complete Linux desktop grouped by display, browser, files, and commands.

## Extends

- [`CommandFilesClient`](CommandFilesClient.md)

## Properties

### browser

> `readonly` **browser**: [`ComputerBrowserClient`](ComputerBrowserClient.md)

______________________________________________________________________

### capabilities

> `readonly` **capabilities**: readonly `string`\[\]

______________________________________________________________________

### computerId

> `readonly` **computerId**: `string`

______________________________________________________________________

### display

> `readonly` **display**: [`ComputerDisplayClient`](ComputerDisplayClient.md)

______________________________________________________________________

### files

> `readonly` **files**: [`SandboxFiles`](SandboxFiles.md)

#### Inherited from

[`CommandFilesClient`](CommandFilesClient.md).[`files`](CommandFilesClient.md#files)

______________________________________________________________________

### sandboxId

> `readonly` **sandboxId**: `string`

______________________________________________________________________

### status

> `readonly` **status**: [`ComputerSessionStatus`](../type-aliases/ComputerSessionStatus.md)

______________________________________________________________________

### template

> `readonly` **template**: `"linux-desktop"`

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
