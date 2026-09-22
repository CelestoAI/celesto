[**@celestoai/celesto**](../README.md)

***

[@celestoai/celesto](../README.md) / CelestoClient

# Interface: CelestoClient

The mockable client contract for creating sandboxes, diagnosing setup, and cleaning up.

## Properties

### browsers

> `readonly` **browsers**: [`BrowserSessionCollection`](BrowserSessionCollection.md)

***

### computers

> `readonly` **computers**: [`ComputerCollection`](ComputerCollection.md)

***

### sandboxes

> `readonly` **sandboxes**: [`SandboxCollection`](SandboxCollection.md)

## Methods

### close()

> **close**(): `Promise`\<`void`\>

#### Returns

`Promise`\<`void`\>

***

### diagnose()

> **diagnose**(): `Promise`\<[`DiagnoseResult`](DiagnoseResult.md)\>

#### Returns

`Promise`\<[`DiagnoseResult`](DiagnoseResult.md)\>
