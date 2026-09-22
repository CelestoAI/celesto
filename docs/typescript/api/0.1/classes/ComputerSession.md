[**@celestoai/celesto**](../README.md)

______________________________________________________________________

[@celestoai/celesto](../README.md) / ComputerSession

# Class: ComputerSession

A complete Linux desktop with grouped display, browser, file, and command access.

## Implements

- [`ComputerSessionClient`](../interfaces/ComputerSessionClient.md)

## Properties

### browser

> `readonly` **browser**: [`ComputerBrowserClient`](../interfaces/ComputerBrowserClient.md)

#### Implementation of

[`ComputerSessionClient`](../interfaces/ComputerSessionClient.md).[`browser`](../interfaces/ComputerSessionClient.md#browser)

______________________________________________________________________

### capabilities

> `readonly` **capabilities**: readonly `string`\[\]

#### Implementation of

[`ComputerSessionClient`](../interfaces/ComputerSessionClient.md).[`capabilities`](../interfaces/ComputerSessionClient.md#capabilities)

______________________________________________________________________

### computerId

> `readonly` **computerId**: `string`

#### Implementation of

[`ComputerSessionClient`](../interfaces/ComputerSessionClient.md).[`computerId`](../interfaces/ComputerSessionClient.md#computerid)

______________________________________________________________________

### display

> `readonly` **display**: [`ComputerDisplayClient`](../interfaces/ComputerDisplayClient.md)

#### Implementation of

[`ComputerSessionClient`](../interfaces/ComputerSessionClient.md).[`display`](../interfaces/ComputerSessionClient.md#display)

______________________________________________________________________

### files

> `readonly` **files**: [`SandboxFiles`](../interfaces/SandboxFiles.md)

#### Implementation of

[`ComputerSessionClient`](../interfaces/ComputerSessionClient.md).[`files`](../interfaces/ComputerSessionClient.md#files)

______________________________________________________________________

### sandboxId

> `readonly` **sandboxId**: `string`

#### Implementation of

[`ComputerSessionClient`](../interfaces/ComputerSessionClient.md).[`sandboxId`](../interfaces/ComputerSessionClient.md#sandboxid)

______________________________________________________________________

### template

> `readonly` **template**: `"linux-desktop"`

#### Implementation of

[`ComputerSessionClient`](../interfaces/ComputerSessionClient.md).[`template`](../interfaces/ComputerSessionClient.md#template)

## Accessors

### status

#### Get Signature

> **get** **status**(): [`ComputerSessionStatus`](../type-aliases/ComputerSessionStatus.md)

##### Returns

[`ComputerSessionStatus`](../type-aliases/ComputerSessionStatus.md)

#### Implementation of

[`ComputerSessionClient`](../interfaces/ComputerSessionClient.md).[`status`](../interfaces/ComputerSessionClient.md#status)

## Methods

### delete()

> **delete**(): `Promise`\<`void`>

#### Returns

`Promise`\<`void`>

#### Implementation of

[`ComputerSessionClient`](../interfaces/ComputerSessionClient.md).[`delete`](../interfaces/ComputerSessionClient.md#delete)

______________________________________________________________________

### exec()

> **exec**(`command`, `options?`): `Promise`\<[`ExecResult`](../interfaces/ExecResult.md)>

#### Parameters

##### command

`string` | readonly `string`\[\]

##### options?

[`ExecOptions`](../interfaces/ExecOptions.md) = `{}`

#### Returns

`Promise`\<[`ExecResult`](../interfaces/ExecResult.md)>

#### Implementation of

[`ComputerSessionClient`](../interfaces/ComputerSessionClient.md).[`exec`](../interfaces/ComputerSessionClient.md#exec)
