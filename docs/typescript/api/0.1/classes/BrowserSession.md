[**@celestoai/celesto**](../README.md)

______________________________________________________________________

[@celestoai/celesto](../README.md) / BrowserSession

# Class: BrowserSession

Run commands in an isolated browser computer owned by one Celesto client. A browser session is the disposable Chromium environment and its private connection endpoints.

## Implements

- [`BrowserSessionClient`](../interfaces/BrowserSessionClient.md)

## Properties

### cdpUrl

> `readonly` **cdpUrl**: `string`

#### Implementation of

[`BrowserSessionClient`](../interfaces/BrowserSessionClient.md).[`cdpUrl`](../interfaces/BrowserSessionClient.md#cdpurl)

______________________________________________________________________

### displayUrl?

> `readonly` `optional` **displayUrl?**: `string`

#### Implementation of

[`BrowserSessionClient`](../interfaces/BrowserSessionClient.md).[`displayUrl`](../interfaces/BrowserSessionClient.md#displayurl)

______________________________________________________________________

### files

> `readonly` **files**: [`SandboxFiles`](../interfaces/SandboxFiles.md)

#### Implementation of

[`BrowserSessionClient`](../interfaces/BrowserSessionClient.md).[`files`](../interfaces/BrowserSessionClient.md#files)

______________________________________________________________________

### profileId?

> `readonly` `optional` **profileId?**: `string`

#### Implementation of

[`BrowserSessionClient`](../interfaces/BrowserSessionClient.md).[`profileId`](../interfaces/BrowserSessionClient.md#profileid)

______________________________________________________________________

### sandboxId

> `readonly` **sandboxId**: `string`

#### Implementation of

[`BrowserSessionClient`](../interfaces/BrowserSessionClient.md).[`sandboxId`](../interfaces/BrowserSessionClient.md#sandboxid)

______________________________________________________________________

### sessionId

> `readonly` **sessionId**: `string`

#### Implementation of

[`BrowserSessionClient`](../interfaces/BrowserSessionClient.md).[`sessionId`](../interfaces/BrowserSessionClient.md#sessionid)

______________________________________________________________________

### viewerUrl?

> `readonly` `optional` **viewerUrl?**: `string`

#### Implementation of

[`BrowserSessionClient`](../interfaces/BrowserSessionClient.md).[`viewerUrl`](../interfaces/BrowserSessionClient.md#viewerurl)

## Accessors

### status

#### Get Signature

> **get** **status**(): [`BrowserSessionStatus`](../type-aliases/BrowserSessionStatus.md)

##### Returns

[`BrowserSessionStatus`](../type-aliases/BrowserSessionStatus.md)

#### Implementation of

[`BrowserSessionClient`](../interfaces/BrowserSessionClient.md).[`status`](../interfaces/BrowserSessionClient.md#status)

## Methods

### delete()

> **delete**(): `Promise`\<`void`>

#### Returns

`Promise`\<`void`>

#### Implementation of

[`BrowserSessionClient`](../interfaces/BrowserSessionClient.md).[`delete`](../interfaces/BrowserSessionClient.md#delete)

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

[`BrowserSessionClient`](../interfaces/BrowserSessionClient.md).[`exec`](../interfaces/BrowserSessionClient.md#exec)
