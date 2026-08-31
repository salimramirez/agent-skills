# Folder structure, naming, and environment

How an Angular app is laid out by bounded context, what every file is called, and where URLs come from.

Organize `src/app/` by **bounded context** (a feature area), and split each context into four layers: `domain`, `application`, `infrastructure`, and `presentation` — the frontend's name for the `interfaces`/inbound layer.

```
src/app/
├── ordering/                            // bounded context
│   ├── domain/
│   │   └── model/
│   │       ├── order.entity.ts          // class Order implements BaseEntity
│   │       └── place-order.command.ts   // class PlaceOrderCommand (non-CRUD intent)
│   ├── application/
│   │   └── ordering.store.ts            // class OrderingStore (state + use cases)
│   ├── infrastructure/
│   │   ├── ordering-api.ts              // class OrderingApi extends BaseApi
│   │   ├── orders-api-endpoint.ts       // class OrdersApiEndpoint extends BaseApiEndpoint
│   │   ├── orders-response.ts           // OrderResource + OrdersResponse
│   │   └── order-assembler.ts           // class OrderAssembler implements BaseAssembler
│   └── presentation/
│       ├── views/                       // routed, smart components
│       │   ├── order-list/              // order-list.ts + .html + .css
│       │   └── order-form/
│       ├── components/                  // reusable, dumb components
│       └── ordering.routes.ts           // export const orderingRoutes
├── catalog/                             // a second context, same four layers
├── identity/
├── shared/                              // the shared kernel — see shared-kernel.md
└── app.routes.ts                        // the root router composes the contexts
```

Dependencies point inward toward `domain`: `presentation`, `application`, and `infrastructure` depend on `domain`; `domain` depends on nothing. Each context owning its own routes, lazy-loaded from the root router, keeps the boundary visible in the routing table too.

## The naming convention

This is the part that makes the code recognizable. The same concept appears in six spellings, and each has one place it belongs.

| Layer | File | Exports | Notes |
| --- | --- | --- | --- |
| domain | `order.entity.ts` | `class Order` | singular, kebab-case file |
| domain | `place-order.command.ts` | `class PlaceOrderCommand` | one file per intent |
| application | `ordering.store.ts` | `class OrderingStore` | named after the **context**, not the entity |
| infrastructure | `orders-response.ts` | `interface OrderResource`, `interface OrdersResponse` | plural file, holds **both** DTOs |
| infrastructure | `order-assembler.ts` | `class OrderAssembler` | singular |
| infrastructure | `orders-api-endpoint.ts` | `class OrdersApiEndpoint` | plural — CRUD over a collection |
| infrastructure | `place-order-endpoint.ts` | `class PlaceOrderApiEndpoint` | singular, no `-api-` — a single action |
| infrastructure | `ordering-api.ts` | `class OrderingApi` | one per context, fronts its endpoints |
| infrastructure | `ordering.guard.ts`, `ordering.interceptor.ts` | `orderingGuard`, `orderingInterceptor` | see `cross-cutting.md` |
| presentation | `ordering.routes.ts` | `const orderingRoutes: Routes` | one per context |
| presentation | `order-list/order-list.ts` | `class OrderList` | **no** `.component.ts` suffix |

Two file names carry real meaning and are easy to blur:

- **`orders-api-endpoint.ts` vs `place-order-endpoint.ts`.** The first is CRUD over a collection and inherits everything from `BaseApiEndpoint`. The second is one action that takes a command; it extends `ErrorHandlingEnabledBaseType` instead. See `commands-and-actions.md`.
- **`orders-response.ts` holds two interfaces**, not one: `OrderResource` is a single item, `OrdersResponse` is the envelope. The file is named after the envelope.

Components follow the current Angular naming: the class is `OrderList`, the file is `order-list.ts`, the selector is `app-order-list`, and the template and styles sit beside it as `order-list.html` and `order-list.css`. There is no `.component` in any of those.

Generate the whole tree for a new context with `scripts/new-context.py` rather than typing the six spellings by hand.

## Where URLs come from

No URL is ever written inside an endpoint. `src/environments/environment.ts` holds one base URL per external provider, plus one path per endpoint, and the endpoint composes them:

```typescript
// src/environments/environment.ts          (production)
export const environment = {
  production: true,
  platformProviderApiBaseUrl: 'https://api.quickbite.example/api/v1',
  platformProviderOrdersEndpointPath: '/orders',
  platformProviderMenuItemsEndpointPath: '/menu-items',
  platformProviderPlaceOrderEndpointPath: '/orders/place'
};
```

```typescript
// src/environments/environment.development.ts
export const environment = {
  production: false,
  platformProviderApiBaseUrl: 'http://localhost:8080/api/v1',
  platformProviderOrdersEndpointPath: '/orders',
  platformProviderMenuItemsEndpointPath: '/menu-items',
  platformProviderPlaceOrderEndpointPath: '/orders/place'
};
```

The key names say **which provider** and **which endpoint**: `<provider>ProviderApiBaseUrl` and `<provider>Provider<Resource>EndpointPath`. `platformProvider` is the app's own backend; a second provider gets its own prefix (`mapsProviderApiBaseUrl`, `paymentsProviderApiBaseUrl`), which keeps it obvious at a glance when a call leaves your own system — and those are exactly the calls that need an anti-corruption layer.

Both files declare the **same keys**; only the values differ. A key present in one and missing from the other is a build error waiting for the other configuration.

## Strategic design on the frontend

- **Bounded contexts** become feature folders — or separate libraries in an Nx workspace. A real app has several, each with its own model, API, store, views, and lazy-loaded routes. When one context needs another — `ordering` needing the signed-in user from `identity` — it goes through that context's store or API, never through its internals, so the boundary holds.
- **Ubiquitous language** runs through the names: `Order`, `OrderingStore`, `OrderingApi`, `PlaceOrderCommand` — the same terms the backend and the domain experts use.
- **The shared kernel** (`shared/`) holds only what every context reuses. Keep it small; see `shared-kernel.md`.
- **Assemblers** are the anti-corruption layer: they stop the shape of whatever you integrate with at the edge of the context.
