# DDD in Angular (frontend)

Read this when structuring an **Angular** app around a domain. Start with the honest part below — DDD on the frontend is *adapted*, not the same as on the backend — and then apply the structure and idioms that follow. Examples use the **QuickBite** food-delivery domain (an `ordering` feature). Idioms follow the Angular 20+ style (standalone components, signals, `inject()`) and apply unchanged on Angular 21 and 22.

> **Angular 22 note.** Everything here stays supported; v22 only *adds* modern alternatives you can opt into without changing this structure: **`@Service()`** as a shorter form of `@Injectable({ providedIn: 'root' })` (root-provided, `inject()`-only) for stores and context APIs; **Signal Forms** alongside the reactive forms shown here; and **`resource()` / `httpResource()`** as a signal-native data-fetching option in place of the manual `subscribe` in the store. Signals also pair naturally with OnPush — the default change detection from v22.

## Contents

- [What DDD means on the frontend](#what-ddd-means-on-the-frontend)
- [Folder structure: bounded contexts and four layers](#folder-structure-bounded-contexts-and-four-layers)
- [The shared kernel](#the-shared-kernel)
- [The domain layer: entities (and commands)](#the-domain-layer-entities-and-commands)
- [Infrastructure: DTOs, assemblers, endpoints, and the context API](#infrastructure-dtos-assemblers-endpoints-and-the-context-api)
- [The application layer: a signal store](#the-application-layer-a-signal-store)
- [The presentation layer: views and components](#the-presentation-layer-views-and-components)
- [Routing](#routing)
- [Reactive forms and writes](#reactive-forms-and-writes)
- [Strategic design on the frontend](#strategic-design-on-the-frontend)
- [What carries over, loosens, or doesn't apply](#what-carries-over-loosens-or-doesnt-apply)

## What DDD means on the frontend

The backend is the **system of record**: it owns the business rules, the invariants, and the transactional consistency. The frontend cannot enforce those — a determined user can bypass any client-side check — so it should not pretend to.

What the frontend *does* gain from DDD is **structure**: organizing the app by the domain (not by technical type), speaking the same **ubiquitous language** as the backend and the experts, keeping a client-side model of the domain separate from the UI, and pushing logic out of components. So treat what follows as **DDD-inspired organization**, not as a place to re-enforce business rules.

## Folder structure: bounded contexts and four layers

Organize `src/app/` by **bounded context** (a feature area), and split each context into four layers: `domain`, `application`, `infrastructure`, and `presentation` — the frontend's name for the `interfaces`/inbound layer.

```
src/app/
├── ordering/                          // bounded context
│   ├── domain/
│   │   └── model/
│   │       └── order.entity.ts        // class: private fields + getters/setters
│   ├── application/
│   │   └── order.store.ts             // signal store (state + use-case orchestration)
│   ├── infrastructure/
│   │   ├── ordering-api.ts            // context API facade (extends BaseApi) — the store uses this
│   │   ├── orders-api-endpoint.ts     // the repository (extends BaseApiEndpoint)
│   │   ├── orders-response.ts         // OrderResource + OrdersResponse (DTOs)
│   │   └── order-assembler.ts         // resource <-> entity (ACL)
│   └── presentation/
│       ├── views/                     // routed, "smart" components (inject the store)
│       ├── components/                // reusable "dumb" components (input()/output())
│       └── ordering.routes.ts         // the context's own lazy-loaded routes
├── shared/                            // the shared kernel (see below)
└── app.routes.ts                      // root router composes the contexts
```

Dependencies point inward toward `domain`: `presentation` and `infrastructure` depend on `domain`; `domain` depends on nothing. Each context owning its own routes (lazy-loaded from the root router) keeps the boundary visible at the routing level too.

## The shared kernel

The `shared/` folder is the **shared kernel** — what genuinely belongs to every context. Unlike on the backend, it spans all four layers, including UI:

```
shared/
├── domain/model/
│   └── base-entity.ts                 // BaseEntity: the { id } every entity carries
├── infrastructure/
│   ├── base-response.ts               // BaseResource / BaseResponse (DTO markers)
│   ├── base-assembler.ts              // BaseAssembler<Entity, Resource, Response>
│   ├── base-api-endpoint.ts           // generic CRUD endpoint
│   └── base-api.ts                    // base for a context's API facade
└── presentation/
    ├── components/                    // Layout (app shell), footer, language switcher, BaseForm
    └── views/                         // app-wide views: home, about, page-not-found
```

- **`domain/model`** — `BaseEntity` is an **interface** (`{ id: number }`); entities `implements BaseEntity`.
- **`infrastructure`** — the base classes the infra layer builds on (detailed in the next section): `BaseResource`/`BaseResponse` (interfaces), `BaseAssembler` (the mapping contract), the generic `BaseApiEndpoint` (CRUD with error handling), and `BaseApi` (a marker the context APIs extend).
- **`presentation`** — this is real UI, and it legitimately belongs to the kernel because every context renders inside it: a **`Layout`** shell (toolbar, nav, `<router-outlet>`), app-wide **views** (`home`, `about`, `page-not-found`), reusable cross-cutting components (a footer, a language switcher), and **`BaseForm`**, a base class form components extend for shared validation-message helpers. It's UI rather than domain, but it's *shared* UI, so it lives here — not in any one context.

Keep the kernel small: base classes, the app shell, and a few app-wide views. Anything specific to one domain belongs in that context.

## The domain layer: entities (and commands)

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

## Infrastructure: DTOs, assemblers, endpoints, and the context API

The infrastructure layer rests on the shared base classes from the kernel: `BaseResource`/`BaseResponse` (DTO markers), `BaseAssembler<Entity, Resource, Response>` (the mapping contract), the generic `BaseApiEndpoint<Entity, Resource, Response, Assembler>` that implements CRUD — `getAll`, `getById`, `create`, `update`, `delete` — with error handling, and `BaseApi` for a context's API facade.

**The DTOs** live in `*-response.ts`: a `Resource` (one item, extends `BaseResource`) and a `Response` (the envelope, extends `BaseResponse`). They mirror the API's wire shape and never leave this layer:

```typescript
// ordering/infrastructure/orders-response.ts
import { BaseResource, BaseResponse } from '../../shared/infrastructure/base-response';

export interface OrderResource extends BaseResource {
  id: number;
  customer_id: number;
  items: { item_id: number; quantity: number }[];
  status: OrderStatus;
  total: number;
}

export interface OrdersResponse extends BaseResponse {
  orders: OrderResource[];
}
```

**The assembler** `implements BaseAssembler` and maps both ways — building entities with `new`, and turning an entity back into a resource for writes:

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

**The context API** (`*-api.ts`, extends `BaseApi`) is the single service the application layer talks to. It owns the context's endpoints (often more than one) and exposes its operations — so the store never touches an endpoint directly:

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

So a read runs `response → toEntitiesFromResponse → entities`, and a create/update runs `entity → toResourceFromEntity → POST/PUT → entity`. For CRUD there's **no separate request DTO** — the resource is the write payload. The assembler is the **anti-corruption layer**: the API's naming and quirks stop here and never reach the domain or the views.

> **Command-style writes.** When a write carries a command rather than an entity (the non-CRUD case), the request body often differs from any resource, so add a dedicated **`*.request.ts`** DTO and an assembler that maps **command → request** (and **response → resource**) — e.g. a `SignInAssembler` with `toRequestFromCommand(command): SignInRequest` and `toResourceFromResponse(response): SignInResource`. Same ACL idea, just for an action instead of a record.

## The application layer: a signal store

The application layer holds **state** and orchestrates **use cases**. A signal-based **store** fills the role command and query handlers play on the backend: it talks to the context API, exposes state through read-only signals, and keeps coordination out of the views.

```typescript
// ordering/application/order.store.ts
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { retry } from 'rxjs';

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

  constructor() { this.loadOrders(); }          // a root store often loads eagerly

  orderById(id: number): Signal<Order | undefined> {
    return computed(() => this.ordersSignal().find(o => o.id === id));   // a reactive query
  }

  loadOrders(): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);
    this.api.getOrders().pipe(takeUntilDestroyed()).subscribe({
      next: orders => { this.ordersSignal.set(orders); this.loadingSignal.set(false); },
      error: () => { this.errorSignal.set('Could not load orders'); this.loadingSignal.set(false); },
    });
  }

  addOrder(order: Order): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);
    this.api.createOrder(order).pipe(retry(2)).subscribe({
      next: created => { this.ordersSignal.update(os => [...os, created]); this.loadingSignal.set(false); },
      error: () => { this.errorSignal.set('Could not create order'); this.loadingSignal.set(false); },
    });
  }
}
```

State is private; the outside reads it through `asReadonly()` signals and `computed()` derivations. `loadOrders`/`activeOrders`/`orderById` are the query side; `addOrder` (and `updateOrder`/`deleteOrder`, same shape) is the command side — each sets `loading`, clears `error`, retries writes, and updates the signal so the UI reflects the change. A new entity is created with `id: 0`; the backend assigns the real id and returns it. The store is also where **cross-entity coordination** lives — e.g. stitching each `Order`'s `Customer` in after a load — keeping that out of the views.

## The presentation layer: views and components

The presentation layer has two kinds of component. A **view** is a routed, "smart" component: it injects the store, reads its signals, and dispatches user actions. A **component** is a reusable, "dumb" piece: it takes data via `input()`, reports intent via `output()`, and knows nothing about the store or the API.

```typescript
// ordering/presentation/views/order-list/order-list.ts  (routed view — talks to the store)
@Component({
  selector: 'app-order-list',
  imports: [OrderItem],
  templateUrl: './order-list.html',
})
export class OrderList {
  private store = inject(OrderStore);
  private router = inject(Router);

  protected readonly orders = this.store.activeOrders;     // a signal, read straight in the template

  deleteOrder(id: number): void { this.store.deleteOrder(id); }
  editOrder(id: number): void { this.router.navigate(['ordering/orders', id, 'edit']); }
}
```

```typescript
// ordering/presentation/components/order-item/order-item.ts  (reusable — no store)
@Component({
  selector: 'app-order-item',
  templateUrl: './order-item.html',
})
export class OrderItem {
  order = input.required<Order>();
  cancel = output<number>();          // emits the id of the order to cancel
}
```

Business or coordination logic in a component is the frontend version of the fat-controller smell — push it into the store. The view stays thin too: it wires the store to the components and handles navigation, nothing more.

## Routing

Each context owns a `*.routes.ts` **inside its `presentation/` folder**, exporting a `Routes` array that lazy-loads its views with `loadComponent`:

```typescript
// ordering/presentation/ordering.routes.ts
import { Routes } from '@angular/router';

const orderList = () => import('./views/order-list/order-list').then(m => m.OrderList);
const orderForm = () => import('./views/order-form/order-form').then(m => m.OrderForm);

export const orderingRoutes: Routes = [
  { path: 'orders',          loadComponent: orderList },
  { path: 'orders/new',      loadComponent: orderForm },
  { path: 'orders/:id/edit', loadComponent: orderForm },
];
```

The root `app.routes.ts` composes the contexts with `loadChildren`, mounts the shared app-wide views, and applies cross-cutting guards:

```typescript
// app.routes.ts
const orderingRoutes = () => import('./ordering/presentation/ordering.routes').then(m => m.orderingRoutes);

export const routes: Routes = [
  { path: 'home',     component: Home, canActivate: [authGuard] },
  { path: 'ordering', loadChildren: orderingRoutes, canActivate: [authGuard] },
  { path: '',         redirectTo: '/home', pathMatch: 'full' },
  { path: '**',       loadComponent: () => import('./shared/presentation/views/page-not-found/page-not-found').then(m => m.PageNotFound) },
];
```

Lazy-loading each context (and each view) keeps the bounded-context boundary visible at the routing level, and the bundles split along it.

## Reactive forms and writes

A reactive form gathers and validates input as **UX** — fast feedback, while the server validates again. For CRUD, the form builds the **entity** and hands it to the store; a form view can `extend BaseForm` to reuse the kernel's validation-message helpers:

```typescript
// ordering/presentation/views/order-form/order-form.ts
export class OrderForm extends BaseForm {
  private fb = inject(FormBuilder);
  private store = inject(OrderStore);
  private router = inject(Router);

  protected form = this.fb.group({
    customerId: new FormControl<number | null>(null, { validators: [Validators.required] }),
    // ...one control group per order item
  });

  submit(): void {
    if (this.form.invalid) return;                       // a UX guard, not the authority
    const order = new Order({
      id: 0, customerId: this.form.value.customerId!, items: [],
      status: 'PLACED', total: 0,
    });
    this.store.addOrder(order);
    this.router.navigate(['ordering/orders']);
  }
}
```

For a **non-CRUD intent**, build a **command** instead and pass it to the store, which sends it through the command→request assembler from the infrastructure section:

```typescript
// identity/presentation/views/sign-in-form/sign-in-form.ts
export class SignInForm extends BaseForm {
  private store = inject(IdentityStore);

  protected form = new FormGroup({
    username: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
    password: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
  });

  signIn(): void {
    if (this.form.invalid) return;
    this.store.signIn(new SignInCommand({
      username: this.form.value.username!, password: this.form.value.password!,
    }));
  }
}
```

Either way: validation feedback stays in the form, the write's shape (entity or command) stays in the domain, and the coordination stays in the store — the view only collects input and dispatches.

## Strategic design on the frontend

- **Bounded contexts** become feature folders (or, in an Nx workspace, separate libraries) — a real app has several (e.g., `ordering`, `identity`, `catalog`), each with its own model, API, store, views, and lazy-loaded routes. When one context needs another — say `ordering` needs the signed-in user from `identity` — it consumes that context's store or service, not its internals, so the boundary holds.
- **Ubiquitous language** runs through the names: `Order`, `OrderStore`, `OrderingApi`, `SignInCommand` — the same terms the backend and the domain experts use.
- **The shared kernel** (`shared/`, see above) holds what every context reuses — base classes, the app shell, and app-wide views — and stays small; most things belong to one context.
- **Assemblers** are the anti-corruption layer: they protect your model from the shape of whatever you integrate with (a backend, a third-party API).

A real app also leans on plumbing that isn't domain modeling: a component library and an i18n pipe in the views (e.g. Angular Material and ngx-translate), and cross-cutting wiring in infrastructure (route guards, HTTP interceptors). Keep it where it belongs — out of the domain and the stores — and don't mistake it for the model.

## What carries over, loosens, or doesn't apply

- **Carries over:** the ubiquitous language; bounded contexts; the four-layer split with an isolated domain; anti-corruption via assemblers; keeping logic out of the UI.
- **Loosens:** repositories are API endpoints rather than aggregate stores; aggregates and value objects are lighter or skipped (the UI rarely needs them); "domain events" are usually signal/observable updates.
- **Doesn't apply:** authoritative invariants and transactional consistency — those belong to the backend. Client-side checks are UX, and the server validates again.
