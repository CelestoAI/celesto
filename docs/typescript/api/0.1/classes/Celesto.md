[**@celestoai/celesto**](../README.md)

***

[@celestoai/celesto](../README.md) / Celesto

# Class: Celesto

Entry point for creating disposable local sandboxes.

## Implements

- [`CelestoClient`](../interfaces/CelestoClient.md)

## Constructors

### Constructor

> **new Celesto**(`options?`): `Celesto`

#### Parameters

##### options?

[`CelestoOptions`](../interfaces/CelestoOptions.md) = `{}`

#### Returns

`Celesto`

## Properties

### browsers

> `readonly` **browsers**: [`BrowserSessionCollection`](../interfaces/BrowserSessionCollection.md)

#### Implementation of

[`CelestoClient`](../interfaces/CelestoClient.md).[`browsers`](../interfaces/CelestoClient.md#browsers)

***

### computers

> `readonly` **computers**: [`ComputerCollection`](../interfaces/ComputerCollection.md)

#### Implementation of

[`CelestoClient`](../interfaces/CelestoClient.md).[`computers`](../interfaces/CelestoClient.md#computers)

***

### sandboxes

> `readonly` **sandboxes**: [`SandboxCollection`](../interfaces/SandboxCollection.md)

#### Implementation of

[`CelestoClient`](../interfaces/CelestoClient.md).[`sandboxes`](../interfaces/CelestoClient.md#sandboxes)

## Methods

### close()

> **close**(): `Promise`\<`void`\>

#### Returns

`Promise`\<`void`\>

#### Implementation of

[`CelestoClient`](../interfaces/CelestoClient.md).[`close`](../interfaces/CelestoClient.md#close)

***

### diagnose()

> **diagnose**(): `Promise`\<[`DiagnoseResult`](../interfaces/DiagnoseResult.md)\>

#### Returns

`Promise`\<[`DiagnoseResult`](../interfaces/DiagnoseResult.md)\>

#### Implementation of

[`CelestoClient`](../interfaces/CelestoClient.md).[`diagnose`](../interfaces/CelestoClient.md#diagnose)
