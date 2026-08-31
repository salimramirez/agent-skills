# The domain layer: entities and commands

Entities as classes with private fields and accessors, and commands for non-CRUD intents.

Model the domain as **classes** named in the ubiquitous language, one per file. An entity lives in `*.entity.ts`, has **private fields**, **accessors**, a constructor taking a **single options object**, and `implements BaseEntity`:

```typescript
// ordering/domain/model/order.entity.ts
import {BaseEntity} from '../../../shared/domain/model/base-entity';

export type OrderStatus = 'PLACED' | 'CONFIRMED' | 'ON_THE_WAY' | 'DELIVERED' | 'CANCELLED';

/** One line of an order: what was ordered, and how many. */
export interface OrderLine {
  menuItemId: number;
  quantity: number;
}

/**
 * An order a customer placed in the ordering context.
 *
 * @remarks
 * The backend owns the invariants — totals and status transitions are decided
 * server-side — so this class holds state and reads well, and does not pretend
 * to enforce rules a determined client could skip.
 */
export class Order implements BaseEntity {
  private _id: number;
  private _customerId: number;
  private _lines: OrderLine[];
  private _deliveryAddress: string;
  private _status: OrderStatus;
  private _total: number;
  private _courierId: number;
  private _courier: Courier | null;

  /**
   * @param order - Initial state, in the language of the ordering context.
   */
  constructor(order: {
    id: number, customerId: number, lines: OrderLine[], deliveryAddress: string,
    status: OrderStatus, total: number, courierId: number, courier?: Courier | null
  }) {
    this._id = order.id;
    this._customerId = order.customerId;
    this._lines = order.lines;
    this._deliveryAddress = order.deliveryAddress;
    this._status = order.status;
    this._total = order.total;
    this._courierId = order.courierId;
    this._courier = order.courier ?? null;
  }

  get id(): number { return this._id; }

  /**
   * @remarks
   * A new order is built with `id: 0`; the backend assigns the real identity
   * and the store writes it back here.
   */
  set id(value: number) { this._id = value; }

  get customerId(): number { return this._customerId; }
  get lines(): OrderLine[] { return this._lines; }
  get deliveryAddress(): string { return this._deliveryAddress; }
  set deliveryAddress(value: string) { this._deliveryAddress = value; }
  get status(): OrderStatus { return this._status; }
  get total(): number { return this._total; }
  get courierId(): number { return this._courierId; }

  /**
   * The courier carrying this order, once the store has resolved it.
   */
  get courier(): Courier | null { return this._courier; }
  set courier(value: Courier | null) { this._courier = value; }
}
```

Three conventions are doing work here.

**Private field plus accessor, not a public field.** It costs a few lines and buys the freedom to add a rule, a derived value, or a log later without touching every caller. Write a `set` **only where the UI genuinely changes the field** — the absence of a setter is a statement, and `total` having none says the client does not get to decide it.

**One options object in the constructor.** Positional parameters of the same type are a bug waiting to happen; `new Order({id, customerId, lines, status, total})` reads at the call site and survives a new field being added.

**Other aggregates by identity.** `_customerId` is a number, not a `Customer`. This is the aggregate rule from the core, and it holds on the client for a practical reason too: the API returns ids, and holding an object would mean the entity could only be built once its neighbour had loaded.

## Resolved related objects

`_courier` is the exception that proves it: `_courierId` stays the source of truth, and the store **stitches in** the resolved `Courier` after both collections have loaded, so a template can show a name instead of a number. The setter exists for the store, not for the UI. See the stitching pattern in `state-store.md`.

## Value objects

A magnitude that carries rules — money with a currency, a delivery window, a quantity with a maximum — can be its own class in `domain/model/`, immutable, with no id. It is worth doing when the rules would otherwise be repeated in several templates. Much of the time the convention keeps these as primitives on the entity, because the backend enforces the rule anyway and the client only formats it. Choose deliberately rather than by habit in either direction.

## Commands

For plain create/update/delete, **the entity is the write payload** — a form builds an `Order` and hands it to the store, and there is no command in sight.

Reach for a **command** when the input is not "save this entity": placing an order from a cart, cancelling with a reason, signing in, anything multi-step. A command is a class too, in `*.command.ts`, with the same encapsulation, named for what the user intends:

```typescript
// ordering/domain/model/place-order.command.ts

/**
 * Intent to place an order for the items currently in a cart.
 *
 * @remarks
 * Not a CRUD write — the request body carries a cart and an address rather
 * than an order, and the backend answers with the order it created.
 */
export class PlaceOrderCommand {
  private _customerId: number;
  private _lines: OrderLine[];
  private _deliveryAddress: string;

  constructor(command: {customerId: number, lines: OrderLine[], deliveryAddress: string}) {
    this._customerId = command.customerId;
    this._lines = command.lines;
    this._deliveryAddress = command.deliveryAddress;
  }

  get customerId(): number { return this._customerId; }
  get lines(): OrderLine[] { return this._lines; }
  get deliveryAddress(): string { return this._deliveryAddress; }
}
```

A command has **no `id`** and does not implement `BaseEntity` — it is not a record, it is a request to do something. Its path through infrastructure is different too; see `commands-and-actions.md`.
