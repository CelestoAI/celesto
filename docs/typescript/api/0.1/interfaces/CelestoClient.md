[**@celestoai/celesto**](../README.md)

______________________________________________________________________

[@celestoai/celesto](../README.md) / CelestoClient

# Interface: CelestoClient

The mockable client contract for creating sandboxes, diagnosing setup, and cleaning up.

## Properties

### browsers

> `readonly` **browsers**: [`BrowserSessionCollection`](BrowserSessionCollection.md)

______________________________________________________________________

### computers

> `readonly` **computers**: [`ComputerCollection`](ComputerCollection.md)

______________________________________________________________________

### sandboxes

> `readonly` **sandboxes**: [`SandboxCollection`](SandboxCollection.md)

## Methods

### close()

> **close**(): `Promise`\<`void`>

#### Returns

`Promise`\<`void`>

______________________________________________________________________

### diagnose()

> **diagnose**(): `Promise`\<[`DiagnoseResult`](DiagnoseResult.md)>

#### Returns

`Promise`\<[`DiagnoseResult`](DiagnoseResult.md)>
