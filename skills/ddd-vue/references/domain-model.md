# The domain layer: entities and commands

Entities as plain classes that carry behaviour, and commands for non-CRUD intents.

Model the domain as **classes** named in the ubiquitous language, one per file, in `domain/model/`. An entity has **public fields**, a constructor taking a **single options object with defaults**, and — this is the part that matters — **behaviour**.

```javascript
// ordering/domain/model/order-line.js

/**
 * One line of an order: what was ordered, and how many.
 *
 * @class OrderLine
 */
export class OrderLine {
    /**
     * @param {Object} params - Line attributes.
     * @param {?number} [params.menuItemId=null] - Identity of the item ordered.
     * @param {number} [params.quantity=0] - How many.
     */
    constructor({menuItemId = null, quantity = 0} = {}) {
        this.menuItemId = menuItemId;
        this.quantity = quantity;
    }
}
```

```javascript
// ordering/domain/model/order.entity.js
import {OrderLine} from './order-line.js';

/**
 * An order placed by a customer in the ordering context.
 *
 * @remarks
 * The backend owns the invariants — totals and status transitions are decided
 * server-side — so this class holds state, reads well, and answers questions
 * about itself. It does not pretend to enforce rules a client could skip.
 *
 * @class Order
 */
export class Order {
    /**
     * @param {Object} params - Entity attributes.
     * @param {?number} [params.id=null] - Identity; null until the backend assigns one.
     * @param {?number} [params.customerId=null] - Identity of the customer.
     * @param {Array<Object>} [params.lines=[]] - Raw line payloads, hydrated below.
     * @param {string} [params.deliveryAddress=''] - Where it goes.
     * @param {string} [params.status='PLACED'] - Lifecycle state.
     * @param {number} [params.total=0] - Amount as the backend computed it.
     */
    constructor({id = null, customerId = null, lines = [],
                 deliveryAddress = '', status = 'PLACED', total = 0} = {}) {
        /** @type {?number} Identity; null until the backend assigns one. */
        this.id = id;
        /** @type {?number} Identity of the customer; another aggregate, held by id. */
        this.customerId = customerId;
        /** @type {OrderLine[]} What was ordered, hydrated into entities. */
        this.lines = lines.map(line => line instanceof OrderLine ? line : new OrderLine(line));
        /** @type {string} Where it goes. */
        this.deliveryAddress = deliveryAddress;
        /** @type {string} Lifecycle state. */
        this.status = status;
        /** @type {number} Amount as the backend computed it. */
        this.total = total;
    }

    /**
     * Whether this order can still be cancelled by the customer.
     *
     * @returns {boolean} True while the kitchen has not dispatched it.
     */
    isCancellable() {
        return this.status === 'PLACED' || this.status === 'CONFIRMED';
    }

    /**
     * How many items the order contains across all its lines.
     *
     * @returns {number} Total quantity.
     */
    itemCount() {
        return this.lines.reduce((count, line) => count + line.quantity, 0);
    }
}
```

Four conventions are doing work here.

**Public fields, not private ones with accessors.** In JavaScript the accessor ceremony buys little: the class is already the boundary, and the JSDoc already states the shape. Spend the effort on behaviour instead.

**One options object with defaults.** `new Order({})` produces a valid, fully-formed object rather than a half-built one, which is exactly what an empty create form needs. Positional parameters of the same type are a bug waiting to happen.

**Hydrate nested entities in the constructor.** `lines` arrives as raw objects and leaves as `OrderLine` instances, so the aggregate is never half-domain and half-payload. Guarding with `instanceof` makes the constructor idempotent — rebuilding an entity from an entity is safe.

**Other aggregates by identity.** `customerId` is a number, not a `Customer`. That is the aggregate rule from the core, and on the client it is also practical: the API returns ids, and holding the object would mean an order could only exist once its neighbour had loaded.

## Give the entity behaviour

`isCancellable()` and `itemCount()` are the point of the class. Without them, `Order` is a bag of fields and every view re-derives the same thing:

```html
<!-- the same rule, spelled out in three templates, drifting apart -->
<button v-if="order.status === 'PLACED' || order.status === 'CONFIRMED'">Cancel</button>
```

That is the **anemic domain model** — the failure the core section names as the most common in DDD, and it is easy to fall into here because nothing forces you out of it. The test is simple: when a rule reads only off an entity's own fields, it belongs on the entity. A rule that needs two aggregates belongs in the store.

Behaviour also covers presentation-shaped questions that are really domain questions — a formatted publication date, a display label, a derived state. Put the method on the entity and let every view call it.

## Value objects

A magnitude that carries rules — money with a currency, a delivery window, a quantity with a maximum — can be its own class in `domain/model/`, with no id and no setters. Worth doing when the rules would otherwise be repeated. Often the convention keeps these as primitives because the backend enforces the rule anyway; choose deliberately rather than by habit.

## Commands

For plain create/update/delete, **the entity is the write payload** — a form builds an `Order` and hands it to the store, and no command is involved.

Reach for a **command** when the input is not "save this entity": placing an order from a cart, cancelling with a reason, signing in. A command is a class too, in `*.command.js`, named for what the user intends:

```javascript
// ordering/domain/model/place-order.command.js

/**
 * Intent to place an order for the items currently in a cart.
 *
 * @remarks
 * Not a CRUD write — the body carries a cart and an address rather than an
 * order, and the backend answers with the order it created.
 *
 * @class PlaceOrderCommand
 */
export class PlaceOrderCommand {
    /**
     * @param {Object} params - Command attributes.
     * @param {number} params.customerId - Who is ordering.
     * @param {Array<Object>} params.lines - What they are ordering.
     * @param {string} params.deliveryAddress - Where it goes.
     */
    constructor({customerId, lines, deliveryAddress}) {
        this.customerId = customerId;
        this.lines = lines;
        this.deliveryAddress = deliveryAddress;
    }
}
```

A command has **no `id`** and no defaults — every field is required, because a half-specified intent is not an intent. Its path through infrastructure differs too; see `commands-and-actions.md`.
