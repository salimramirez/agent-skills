# DDD in Angular (frontend)

Read this when structuring an **Angular** app around a domain. Start with the honest part below — DDD on the frontend is *adapted*, not the same as on the backend — and then apply the structure and idioms that follow. Examples use the **QuickBite** food-delivery domain (an `ordering` feature). Idioms are Angular 20-style (standalone components, signals, `inject()`).

## Contents

- [What DDD means on the frontend](#what-ddd-means-on-the-frontend)
- [Folder structure: bounded contexts and four layers](#folder-structure-bounded-contexts-and-four-layers)
- [The domain layer: entities and commands](#the-domain-layer-entities-and-commands)
- [Infrastructure: endpoints, DTOs, assemblers, and the context API](#infrastructure-endpoints-dtos-assemblers-and-the-context-api)
- [The application layer: a signal store](#the-application-layer-a-signal-store)
- [The presentation layer](#the-presentation-layer)
- [Reactive forms](#reactive-forms)
- [Strategic design on the frontend](#strategic-design-on-the-frontend)
- [What carries over, loosens, or doesn't apply](#what-carries-over-loosens-or-doesnt-apply)

## What DDD means on the frontend

The backend is the **system of record**: it owns the business rules, the invariants, and the transactional consistency. The frontend cannot enforce those — a determined user can bypass any client-side check — so it should not pretend to.

What the frontend *does* gain from DDD is **structure**: organizing the app by the domain (not by technical type), speaking the same **ubiquitous language** as the backend and the experts, keeping a client-side model of the domain separate from the UI, and pushing logic out of components. So treat what follows as **DDD-inspired organization**, not as a place to re-enforce business rules.

## Folder structure: bounded contexts and four layers

Organize `src/app/` by **bounded context** (a feature area), and split each context into four layers: `domain`, `application`, `infrastructure`, and `presentation` — the frontend's name for the `interfaces`/inbound layer. A `shared/` folder holds the shared kernel, including the base classes the others build on.

```
src/app/
├── ordering/                          // bounded context
│   ├── domain/
│   │   └── model/
│   │       ├── order.entity.ts        // class: private fields + getters/setters
│   │       └── place-order.command.ts // class: a command object
│   ├── application/                   // signal stores (use-case orchestration)
│   ├── infrastructure/
│   │   ├── ordering-api.ts            // context API facade (extends BaseApi) — the store uses this
│   │   ├── orders-api-endpoint.ts     // the repository (extends BaseApiEndpoint)
│   │   ├── orders-response.ts          // OrderResource + OrdersResponse (DTOs)
│   │   └── order-assembler.ts          // resource <-> entity (ACL)
│   ├── presentation/                  // components and pages (the UI)
│   └── ordering.routes.ts             // the context's own lazy-loaded routes
└── shared/                            // base classes: BaseEntity, BaseResource/BaseResponse,
                                       // BaseAssembler, BaseApiEndpoint, BaseApi
```

Dependencies point inward toward `domain`: `presentation` and `infrastructure` depend on `domain`; `domain` depends on nothing. Each context owning its own `*.routes.ts` (lazy-loaded from the app router) keeps the boundary visible at the routing level too.

## The domain layer: entities and commands

Model the domain as **classes** named in the ubiquitous language. The convention puts each entity in a `*.entity.ts` file with **private fields**, **getters/setters**, and a constructor that takes a single options object:

```typescript
// ordering/domain/model/order.entity.ts
export type OrderStatus = 'PLACED' | 'CONFIRMED' | 'DELIVERED' | 'CANCELLED';

export class Order {
  private _id: number;
  private _customerId: number;        // another aggregate, referenced by id
  private _items: { itemId: number; quantity: number }[];
  private _status: OrderStatus;
  private _total: number;
  private _placedAt: string;

  constructor(order: {
    id: number; customerId: number; items: { itemId: number; quantity: number }[];
    status: OrderStatus; total: number; placedAt: string;
  }) {
    this._id = order.id;
    this._customerId = order.customerId;
    this._items = order.items;
    this._status = order.status;
    this._total = order.total;
    this._placedAt = order.placedAt;
  }

  get id(): number { return this._id; }
  get customerId(): number { return this._customerId; }
  get items(): { itemId: number; quantity: number }[] { return this._items; }
  get status(): OrderStatus { return this._status; }
  set status(value: OrderStatus) { this._status = value; }
  get total(): number { return this._total; }
  get placedAt(): string { return this._placedAt; }
}
```

An entity can extend a shared `BaseEntity` that carries the `id`. On the frontend these stay thin — the backend owns the invariants — so a `set` exists only where the UI genuinely mutates the field. A magnitude with rules (money, a quantity range) can become its own value-object class, though the convention often keeps them as primitives.

A **command** is also a class (`*.command.ts`), with the same encapsulation. It captures an intent to change state — what a form submits:

```typescript
// ordering/domain/model/place-order.command.ts
export class PlaceOrderCommand {
  private _customerId: number;
  private _items: { itemId: number; quantity: number }[];

  constructor(command: { customerId: number; items: { itemId: number; quantity: number }[] }) {
    this._customerId = command.customerId;
    this._items = command.items;
  }

  get customerId(): number { return this._customerId; }
  get items(): { itemId: number; quantity: number }[] { return this._items; }
}
```

## Infrastructure: endpoints, DTOs, assemblers, and the context API

The infrastructure layer rests on a few **shared base classes** (in `shared/`): `BaseEntity` (an `id`), `BaseResource`/`BaseResponse` (DTO markers), `BaseAssembler<Entity, Resource, Response>` (the mapping contract), a generic `BaseApiEndpoint<Entity, Resource, Response, Assembler>` that implements CRUD — `getAll`, `getById`, `create`, `update`, `delete` — with error handling, and `BaseApi` for a context's API facade.

**The DTOs** live in `*-response.ts`: a `Resource` (one item, extends `BaseResource`) and a `Response` (the envelope, extends `BaseResponse`). They mirror the API and never leave this layer:

```typescript
// ordering/infrastructure/orders-response.ts
import { BaseResource, BaseResponse } from '../../shared/infrastructure/base-response';

export interface OrderResource extends BaseResource {
  id: number;
  customer_id: number;
  items: { item_id: number; quantity: number }[];
  status: OrderStatus;
  total: number;
  placed_at: string;
}

export interface OrdersResponse extends BaseResponse {
  orders: OrderResource[];
}
```

**The assembler** implements `BaseAssembler` and maps both ways — building entities with `new`, and turning an entity back into a resource for writes:

```typescript
// ordering/infrastructure/order-assembler.ts
import { BaseAssembler } from '../../shared/infrastructure/base-assembler';

export class OrderAssembler implements BaseAssembler<Order, OrderResource, OrdersResponse> {
  toEntityFromResource(resource: OrderResource): Order {
    return new Order({
      id: resource.id,
      customerId: resource.customer_id,                                  // translate the API's naming
      items: resource.items.map(i => ({ itemId: i.item_id, quantity: i.quantity })),
      status: resource.status,
      total: resource.total,
      placedAt: resource.placed_at,
    });
  }

  toEntitiesFromResponse(response: OrdersResponse): Order[] {
    return response.orders.map(resource => this.toEntityFromResource(resource));
  }

  toResourceFromEntity(entity: Order): OrderResource {
    return {
      id: entity.id,
      customer_id: entity.customerId,
      items: entity.items.map(i => ({ item_id: i.itemId, quantity: i.quantity })),
      status: entity.status,
      total: entity.total,
      placed_at: entity.placedAt,
    } as OrderResource;
  }
}
```

**The endpoint** is the repository — it declares only its URL and assembler; the CRUD comes from the base class:

```typescript
// ordering/infrastructure/orders-api-endpoint.ts
export class OrdersApiEndpoint extends BaseApiEndpoint<Order, OrderResource, OrdersResponse, OrderAssembler> {
  constructor(http: HttpClient) {
    super(http, `${environment.apiBaseUrl}/orders`, new OrderAssembler());
  }
}
```

**The context API** (`*-api.ts`, extends `BaseApi`) is the single service the application layer talks to. It owns the context's endpoints and exposes its operations — so the store never touches an endpoint directly:

```typescript
// ordering/infrastructure/ordering-api.ts
@Injectable({ providedIn: 'root' })
export class OrderingApi extends BaseApi {
  private readonly orders: OrdersApiEndpoint;

  constructor(http: HttpClient) {
    super();
    this.orders = new OrdersApiEndpoint(http);
  }

  getOrders(): Observable<Order[]> { return this.orders.getAll(); }
  createOrder(order: Order): Observable<Order> { return this.orders.create(order); }
  updateOrder(order: Order): Observable<Order> { return this.orders.update(order, order.id); }
  deleteOrder(id: number): Observable<void> { return this.orders.delete(id); }
}
```

So a read runs `response → toEntitiesFromResponse → entities`, and a create/update runs `entity → toResourceFromEntity → POST/PUT → entity`. There is no separate request DTO — the resource is the write payload. The assembler is the **anti-corruption layer**: the API's naming and quirks stop here and never reach the domain or the components. (`BaseForm`, in `shared/presentation`, plays the same boilerplate-cutting role for reactive-form validation messages; cross-cutting plumbing like an auth guard or HTTP interceptor also lives in infrastructure, but it is framework wiring, not domain modeling.)

## The application layer: a signal store

The application layer holds **state** and orchestrates **use cases**. A signal-based **store** fills the role command and query handlers play on the backend: it talks to the context API, exposes state, and keeps coordination out of the components.

```typescript
// ordering/application/order.store.ts
@Injectable({ providedIn: 'root' })
export class OrderStore {
  private api = inject(OrderingApi);

  private readonly ordersSignal = signal<Order[]>([]);
  private readonly loadingSignal = signal(false);
  private readonly errorSignal = signal<string | null>(null);

  readonly orders = this.ordersSignal.asReadonly();
  readonly loading = this.loadingSignal.asReadonly();
  readonly error = this.errorSignal.asReadonly();
  readonly activeOrders = computed(() =>
    this.ordersSignal().filter(o => o.status !== 'DELIVERED' && o.status !== 'CANCELLED'));

  orderById(id: number): Signal<Order | undefined> {
    return computed(() => this.ordersSignal().find(o => o.id === id));   // a reactive query
  }

  loadOrders(): void {
    this.loadingSignal.set(true);
    this.api.getOrders().subscribe({
      next: orders => { this.ordersSignal.set(orders); this.loadingSignal.set(false); },
      error: () => { this.errorSignal.set('Could not load orders'); this.loadingSignal.set(false); },
    });
  }

  placeOrder(command: PlaceOrderCommand): void {
    const order = new Order({
      id: 0, customerId: command.customerId, items: command.items,
      status: 'PLACED', total: 0, placedAt: '',
    });
    this.api.createOrder(order).subscribe(created => this.ordersSignal.update(c => [created, ...c]));
  }
}
```

State is private; the outside reads it through `asReadonly()` signals and `computed()` derivations. `loadOrders`/`activeOrders`/`orderById` are the query side; `placeOrder` is the command side, and `update`/`delete` follow the same shape. A new entity is created with `id: 0` — the backend assigns the real id and returns it.

## The presentation layer

Keep components **thin**: they render inputs and emit events, and delegate everything else to the store. Presentational components take data via `input()` and report user intent via `output()`, with no knowledge of the API or the store.

```typescript
// ordering/presentation/components/order-list/order-list.ts
@Component({
  selector: 'app-order-list',
  imports: [OrderItem],
  templateUrl: './order-list.html',
})
export class OrderList {
  orders = input.required<Order[]>();
  cancel = output<number>();          // emits the id of the order to cancel
}
```

A **container** (page) component is the one place that touches the store, wiring it to the presentational components:

```typescript
// ordering/presentation/pages/orders-page/orders-page.ts
@Component({
  selector: 'app-orders-page',
  imports: [OrderList],
  templateUrl: './orders-page.html',
})
export class OrdersPage implements OnInit {
  private store = inject(OrderStore);
  protected readonly orders = this.store.activeOrders;

  ngOnInit(): void {
    this.store.loadOrders();
  }
}
```

Business or coordination logic in a component is the frontend version of the anemic-vs-fat-controller smell — push it into the store.

## Reactive forms

A reactive form gathers and validates input as **UX** — fast feedback, while the server validates again — then builds a command and hands it to the store:

```typescript
// ordering/presentation/pages/new-order-page/new-order-page.ts
export class NewOrderPage {
  private fb = inject(FormBuilder);
  private store = inject(OrderStore);

  protected form = this.fb.group({
    customerId: [null as number | null, Validators.required],
    // ...one control group per order item
  });

  submit(): void {
    if (this.form.invalid) return;                       // a UX guard, not the authority
    const { customerId } = this.form.getRawValue();
    this.store.placeOrder(new PlaceOrderCommand({ customerId: customerId!, items: [] }));
  }
}
```

Keep the validation feedback in the form, the command's shape in the domain, and the coordination in the store — the component only collects input and dispatches.

## Strategic design on the frontend

- **Bounded contexts** become feature folders (or, in an Nx workspace, separate libraries) — a real app has several (e.g., `ordering`, `identity`, `catalog`), each with its own model, API, UI, and lazy-loaded routes. When one context needs another — say `ordering` needs the signed-in user from `identity` — it consumes that context's store or service, not its internals, so the boundary holds.
- **Ubiquitous language** runs through the names: `Order`, `PlaceOrderCommand`, `OrderStore`, `OrderingApi` — the same terms the backend and the domain experts use.
- The **shared kernel** (`shared/`) holds what genuinely belongs to every context: the base classes (`BaseEntity`, `BaseAssembler`, `BaseApiEndpoint`, `BaseApi`, `BaseForm`) and cross-context types. Keep it small — most things belong to one context.
- **Assemblers** are the anti-corruption layer: they protect your model from the shape of whatever you integrate with (a backend, a third-party API).

## What carries over, loosens, or doesn't apply

- **Carries over:** the ubiquitous language; bounded contexts; the four-layer split with an isolated domain; anti-corruption via assemblers; keeping logic out of the UI.
- **Loosens:** repositories are API endpoints rather than aggregate stores; aggregates and value objects are lighter or skipped (the UI rarely needs them); "domain events" are usually signal/observable updates.
- **Doesn't apply:** authoritative invariants and transactional consistency — those belong to the backend. Client-side checks are UX, and the server validates again.
