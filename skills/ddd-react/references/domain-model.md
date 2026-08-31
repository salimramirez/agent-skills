# The domain layer: entities and commands

Entities as immutable classes that carry behaviour, and commands for non-CRUD intents.

Model the domain as **classes** named in the ubiquitous language, one per file, in `domain/model/`. A React entity has **`readonly` fields**, a constructor taking a **single options object with defaults**, **behaviour**, and `with…` methods for change.

```typescript
// ordering/domain/model/order.entity.ts
import {OrderLine} from './order-line';

export type OrderStatus = 'PLACED' | 'CONFIRMED' | 'ON_THE_WAY' | 'DELIVERED' | 'CANCELLED';

/** Attributes an order is built from. */
export interface OrderAttributes {
    id?: number | null;
    customerId?: number | null;
    lines?: Array<OrderLine | {menuItemId: number; quantity: number}>;
    deliveryAddress?: string;
    status?: OrderStatus;
    total?: number;
}

/**
 * An order placed by a customer in the ordering context.
 *
 * Every field is `readonly`. React decides what to re-render by reference identity,
 * so an entity mutated in place changes nothing on screen — changes produce a new
 * instance through the `with…` methods below.
 *
 * The backend owns the invariants — totals and status transitions are decided
 * server-side — so this class holds state, answers questions about itself, and does
 * not pretend to enforce rules a client could skip.
 */
export class Order {
    readonly id: number | null;
    readonly customerId: number | null;
    readonly lines: readonly OrderLine[];
    readonly deliveryAddress: string;
    readonly status: OrderStatus;
    readonly total: number;

    constructor({
        id = null, customerId = null, lines = [],
        deliveryAddress = '', status = 'PLACED', total = 0
    }: OrderAttributes = {}) {
        this.id = id;
        this.customerId = customerId;
        this.lines = lines.map(line => line instanceof OrderLine ? line : new OrderLine(line));
        this.deliveryAddress = deliveryAddress;
        this.status = status;
        this.total = total;
    }

    /** Whether the customer can still cancel, per the status the backend reported. */
    isCancellable(): boolean {
        return this.status === 'PLACED' || this.status === 'CONFIRMED';
    }

    /** How many items the order contains across all its lines. */
    itemCount(): number {
        return this.lines.reduce((count, line) => count + line.quantity, 0);
    }

    /** A copy of this order with a different delivery address. */
    withDeliveryAddress(deliveryAddress: string): Order {
        return new Order({...this, lines: [...this.lines], deliveryAddress});
    }
}
```

## Why immutable, specifically

This is the one rule React forces that Angular and Vue do not.

React decides what to re-render by comparing references. Mutating an entity in place leaves the reference untouched, so **the screen does not update** — no error, no warning, just stale UI. Measured, not assumed: mutating a field on an entity held in a store leaves the rendered value at its old text, while replacing the instance updates it.

`readonly` turns that from a discipline into a compile error, and `with…` methods make the correct path the easy one. It is also the more DDD-correct design: an entity that can only be replaced is one whose transitions you can name.

Note the `[...this.lines]` in `withDeliveryAddress`: `readonly OrderLine[]` is not assignable to the mutable array the constructor accepts, so the copy is deliberate.

## Give the entity behaviour

`isCancellable()` and `itemCount()` are the point of the class. Without them, `Order` is a bag of fields and every component re-derives the same thing:

```tsx
{/* the same rule, spelled out in three components, drifting apart */}
{(order.status === 'PLACED' || order.status === 'CONFIRMED') && <button>Cancel</button>}
```

That is the **anemic domain model** — the failure the core section names as the most common in DDD.

In TypeScript, behaviour buys something extra and concrete. TypeScript's type system is *structural*: an anemic entity is just a shape, so any lookalike object satisfies it — including a raw API resource. Add methods and it no longer does. Passing a resource where an `Order` is expected produces:

```
TS2739: Type '{ id: number; customer_id: number; … }' is missing the following
properties from type 'Order': customerId, deliveryAddress, isCancellable, itemCount
```

The compiler names the missing *methods*. Entity behaviour is what makes the anti-corruption boundary enforceable rather than merely documented.

## Nested entities and neighbouring aggregates

`lines` arrives as raw objects and leaves as `OrderLine` instances, so the aggregate is never half-domain and half-payload. Guarding with `instanceof` makes the constructor idempotent — rebuilding an entity from an entity is safe, which matters because `with…` methods spread `this`.

`customerId` is a number, not a `Customer`. That is the aggregate rule from the core, and on the client it is also practical: the API returns ids, and holding the object would mean an order could only exist once its neighbour had loaded.

## Value objects

A magnitude that carries rules — money with a currency, a delivery window — can be its own class in `domain/model/`, with no id. In React they are already immutable by default, so the pattern costs nothing beyond the file. Worth doing when the rules would otherwise be repeated.

## Commands

For plain create/update/delete, **the entity is the write payload** — a form builds an `Order` and hands it to the store, and no command is involved.

Reach for a **command** when the input is not "save this entity": placing an order from a cart, cancelling with a reason, signing in. A command is a class too, in `*.command.ts`, named for what the user intends:

```typescript
// ordering/domain/model/place-order.command.ts
import type {OrderLine} from './order-line';

/**
 * Intent to place an order for the items currently in a cart.
 *
 * Not a CRUD write — the body carries a cart and an address rather than an order,
 * and the backend answers with the order it created.
 */
export class PlaceOrderCommand {
    readonly customerId: number;
    readonly lines: readonly OrderLine[];
    readonly deliveryAddress: string;

    constructor({customerId, lines, deliveryAddress}: {
        customerId: number;
        lines: readonly OrderLine[];
        deliveryAddress: string;
    }) {
        this.customerId = customerId;
        this.lines = lines;
        this.deliveryAddress = deliveryAddress;
    }
}
```

A command has **no `id`** and no defaults — every field is required, because a half-specified intent is not an intent. Its path through infrastructure differs too; see `commands-and-actions.md`.
