# The domain layer: entities and commands

Entities as classes with private fields and accessors, and commands for non-CRUD intents.

Model the domain as **classes** named in the ubiquitous language. The convention puts each entity in a `*.entity.ts` file with **private fields**, **getters/setters**, and a constructor that takes a single options object. An entity `implements BaseEntity` (the shared `{ id }` interface):

```typescript
// ordering/domain/model/order.entity.ts
import { BaseEntity } from '../../../shared/domain/model/base-entity';

export type OrderStatus = 'PLACED' | 'CONFIRMED' | 'DELIVERED' | 'CANCELLED';

export class Order implements BaseEntity {
  private _id: number;
  private _customerId: number;        // another aggregate, referenced by id
  private _items: { itemId: number; quantity: number }[];
  private _status: OrderStatus;
  private _total: number;

  constructor(order: {
    id: number; customerId: number; items: { itemId: number; quantity: number }[];
    status: OrderStatus; total: number;
  }) {
    this._id = order.id;
    this._customerId = order.customerId;
    this._items = order.items;
    this._status = order.status;
    this._total = order.total;
  }

  get id(): number { return this._id; }
  set id(value: number) { this._id = value; }     // the backend assigns it after create
  get customerId(): number { return this._customerId; }
  get items(): { itemId: number; quantity: number }[] { return this._items; }
  get status(): OrderStatus { return this._status; }
  set status(value: OrderStatus) { this._status = value; }
  get total(): number { return this._total; }
}
```

On the frontend entities stay thin — the backend owns the invariants — so a `set` exists only where the UI genuinely mutates the field. A magnitude with rules (money, a quantity range) can become its own value-object class, though the convention often keeps these as primitives. An entity may also hold a **resolved related object** (e.g. an `Order` carrying its `Customer`) that the store stitches in after loading; the raw id stays the source of truth.

For straightforward create/update/delete, the **entity itself is the write payload** — a form builds an `Order` and hands it to the store; there's no separate command. Reach for a **command** only for a **non-CRUD intent** — signing in, a multi-step action, anything where the input isn't just "save this entity." A command is a class too (`*.command.ts`), with the same encapsulation, capturing what the user intends:

```typescript
// identity/domain/model/sign-in.command.ts
export class SignInCommand {
  private _username: string;
  private _password: string;

  constructor(input: { username: string; password: string }) {
    this._username = input.username;
    this._password = input.password;
  }

  get username(): string { return this._username; }
  get password(): string { return this._password; }
}
```
