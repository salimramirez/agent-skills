# If your project is JavaScript

What changes when there is no compiler, and what has to replace it.

This skill is written in TypeScript, and one rule depends on it: typing a prop as `Order` is what makes a skipped assembler a compile error. In JavaScript that check does not exist — React 19 removed `propTypes` validation and **silently ignores** it, and React's own upgrade guide points at TypeScript as the replacement.

Everything else transfers unchanged. The structure, the four layers, the naming, the assemblers, the Zustand store, the path builders, the loaders — none of that is TypeScript.

## Types become JSDoc

Drop the annotations and describe the shape in a doc block. The editor still reads it, and `// @ts-check` at the top of a file turns it into real checking without adopting TypeScript.

```javascript
// ordering/domain/model/order.entity.js

/**
 * @typedef {Object} OrderAttributes
 * @property {?number} [id]
 * @property {?number} [customerId]
 * @property {string} [deliveryAddress]
 * @property {'PLACED'|'CONFIRMED'|'ON_THE_WAY'|'DELIVERED'|'CANCELLED'} [status]
 */

export class Order {
    /** @param {OrderAttributes} attributes */
    constructor({id = null, customerId = null, deliveryAddress = '', status = 'PLACED'} = {}) {
        this.id = id;
        this.customerId = customerId;
        this.deliveryAddress = deliveryAddress;
        this.status = status;
    }

    /** @returns {boolean} Whether the customer can still cancel. */
    isCancellable() {
        return this.status === 'PLACED' || this.status === 'CONFIRMED';
    }
}
```

Two things get weaker and are worth naming. `readonly` is gone, so entity immutability becomes a convention you enforce by review rather than by compiler — `Object.freeze(this)` at the end of the constructor is the runtime substitute, at a small cost. And resource interfaces have no runtime existence in either language, so in JavaScript they simply become documentation.

## The anti-corruption check moves to the assembler

This is the important substitution. Without types, nothing stops a raw resource reaching a component — so put a **runtime schema check where untrusted data enters**, which is the assembler. That is a better place than a prop type anyway: it is the actual boundary.

```javascript
// ordering/infrastructure/order.assembler.js
import {z} from 'zod';
import {Order} from '../domain/model/order.entity.js';

const orderResourceSchema = z.object({
    id: z.number(),
    customer_id: z.number(),
    delivery_address: z.string(),
    status: z.string()
});

export class OrderAssembler {
    static toEntityFromResource(resource) {
        const parsed = orderResourceSchema.parse(resource);   // throws on a shape change
        return new Order({
            id: parsed.id,
            customerId: parsed.customer_id,
            deliveryAddress: parsed.delivery_address,
            status: parsed.status
        });
    }

    static toEntitiesFromResponse(response) {
        if (response.status !== 200) return [];
        const resources = Array.isArray(response.data) ? response.data : response.data['orders'] ?? [];
        return resources.map(resource => this.toEntityFromResource(resource));
    }
}
```

`parse` throws, which the store's `catch` already records — so a backend that renames a field surfaces as a visible error naming the field, instead of `undefined` spreading quietly through three components.

Worth knowing: a TypeScript project benefits from this too. Types describe what you *expect* from the network, not what arrived. `commands-and-actions.md` notes the same gap where a response is asserted rather than checked.

## File extensions

`.js` and `.jsx`; component files stay PascalCase (`OrderList.jsx`), everything else keeps the dot/dash rule. The generator emits TypeScript, so a JavaScript project either renames and strips annotations — mechanical, and the shapes are all in the doc blocks above — or copies the structure by hand from `structure.md`.
