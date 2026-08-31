# Folder structure, naming, and environment

How a Vue app is laid out by bounded context, what every file is called, and where URLs come from.

Organize `src/` by **bounded context** (a feature area), and split each context into four layers: `domain`, `application`, `infrastructure`, and `presentation` — the frontend's name for the `interfaces`/inbound layer.

```
src/
├── ordering/                          // bounded context
│   ├── domain/
│   │   └── model/
│   │       ├── order.entity.js        // class Order
│   │       └── place-order.command.js // class PlaceOrderCommand
│   ├── application/
│   │   └── ordering.store.js          // useOrderingStore (Pinia)
│   ├── infrastructure/
│   │   ├── ordering-api.js            // class OrderingApi extends BaseApi
│   │   └── order.assembler.js         // class OrderAssembler (static)
│   └── presentation/
│       ├── views/                     // routed, smart components
│       │   ├── order-list.vue
│       │   └── order-form.vue
│       ├── components/                // reusable, dumb components
│       └── ordering-routes.js         // export default orderingRoutes
├── identity/                          // a second context, same four layers
├── shared/                            // the shared kernel — see shared-kernel.md
├── router.js                          // composes the contexts
├── pinia.js
└── main.js
```

Dependencies point inward toward `domain`: `presentation`, `application`, and `infrastructure` depend on `domain`; `domain` depends on nothing — not on Vue, not on axios, not on the router. Each context owning its routes keeps the boundary visible in the routing table too.

Entities live in `domain/model/`, and so do commands. Keep them together: a command is part of the domain's vocabulary, not a transport detail.

## The naming convention

Two separators, and each means something:

- **A dot** when the suffix names the kind of building block — `order.entity.js`, `order.assembler.js`, `place-order.command.js`, `ordering.store.js`, `authentication.guard.js`, `identity.interceptor.js`.
- **A dash** when the name itself is compound — `ordering-api.js`, `ordering-routes.js`, `base-endpoint.js`.

| Layer | File | Exports |
| --- | --- | --- |
| domain | `order.entity.js` | `class Order` |
| domain | `place-order.command.js` | `class PlaceOrderCommand` |
| application | `ordering.store.js` | `useOrderingStore` (default export) |
| infrastructure | `order.assembler.js` | `class OrderAssembler`, static methods |
| infrastructure | `ordering-api.js` | `class OrderingApi extends BaseApi` |
| infrastructure | `place-order.resource.js` | `class PlaceOrderResource` |
| infrastructure | `authentication.guard.js` | `authenticationGuard` |
| infrastructure | `identity.interceptor.js` | `identityInterceptor` |
| presentation | `ordering-routes.js` | `orderingRoutes` (default export) |
| presentation | `views/order-list.vue` | component `OrderList` |
| presentation | `components/order-card.vue` | component `OrderCard` |

Single-file components are **kebab-case**, always. Vue's style guide accepts either kebab-case or PascalCase and asks only for consistency; kebab keeps the `.vue` files from being the only capitalized names in the tree, and sidesteps case-insensitive filesystems. The import binds the PascalCase name you use in the template:

```javascript
import OrderCard from './components/order-card.vue';
```

A store is named after the **context**, not the entity: `useOrderingStore` holds orders and menu items alike. One store per context is the rule; see `state-store.md`.

Generate the tree for a new context with `scripts/new-context.py` rather than typing the six spellings of the name by hand.

## Where URLs come from

No URL is written inside a gateway. Vite exposes anything prefixed `VITE_` on `import.meta.env`, so one base URL per provider plus one path per endpoint lives in the env files:

```bash
# .env.development
VITE_PLATFORM_API_URL="http://localhost:8080/api/v1"
VITE_ORDERS_ENDPOINT_PATH="/orders"
VITE_MENU_ITEMS_ENDPOINT_PATH="/menu-items"
```

```bash
# .env.production
VITE_PLATFORM_API_URL="https://api.quickbite.example/api/v1"
VITE_ORDERS_ENDPOINT_PATH="/orders"
VITE_MENU_ITEMS_ENDPOINT_PATH="/menu-items"
```

The keys say **which provider** and **which endpoint**: `VITE_PLATFORM_API_URL` is your own backend; a third party gets its own prefix (`VITE_MAPS_API_URL`, `VITE_PAYMENTS_API_URL`). That makes it obvious at a glance when a call leaves your system — and those are exactly the calls that need an anti-corruption layer.

Both files declare the **same keys**; only the values differ. A key missing from one of them is `undefined` at runtime, and axios turns an undefined `baseURL` into a **relative** request against the app's own origin — so the call quietly hits your dev server and comes back with `index.html` or a 404, never an error that names the missing key.

> **Secrets.** Everything prefixed `VITE_` is inlined into the bundle and readable by anyone. Fine for a public, rate-limited provider; anything that must stay secret belongs behind your own backend.

## Strategic design on the frontend

- **Bounded contexts** become feature folders. A real app has several — `ordering`, `catalog`, `identity` — each with its own model, gateway, store, views, and routes. When one context needs another, it goes through that context's store, never its internals.
- **Ubiquitous language** runs through the names: `Order`, `useOrderingStore`, `OrderingApi`, `PlaceOrderCommand`.
- **The shared kernel** (`shared/`) holds only what every context reuses, and stays small.
- **Assemblers** are the anti-corruption layer: the shape of whatever you integrate with stops at the edge of the context.
