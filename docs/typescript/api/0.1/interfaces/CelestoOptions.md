[**@celestoai/celesto**](../README.md)

______________________________________________________________________

[@celestoai/celesto](../README.md) / CelestoOptions

# Interface: CelestoOptions

Configure runtime startup, lifecycle events, debugging, or a test transport.

## Properties

### createTimeoutMs?

> `optional` **createTimeoutMs?**: `number`

Time allowed to download an image and create a sandbox.

______________________________________________________________________

### debug?

> `optional` **debug?**: `boolean`

Retain non-enumerable causes on CelestoError instances.

______________________________________________________________________

### onEvent?

> `optional` **onEvent?**: (`event`) => `void`

Observe typed lifecycle events.

#### Parameters

##### event

[`CelestoEvent`](../type-aliases/CelestoEvent.md)

#### Returns

`void`

______________________________________________________________________

### requestTimeoutMs?

> `optional` **requestTimeoutMs?**: `number`

Time allowed for ordinary bridge requests that do not manage a VM lifecycle operation.

______________________________________________________________________

### runtimePath?

> `optional` **runtimePath?**: `string`

Runtime executable path. Defaults to `celesto` on PATH.

______________________________________________________________________

### startupTimeoutMs?

> `optional` **startupTimeoutMs?**: `number`

Time allowed for the local bridge to start.

______________________________________________________________________

### transport?

> `optional` **transport?**: [`CelestoTransport`](CelestoTransport.md)

Supply a structural transport in tests; normal applications should omit this.
