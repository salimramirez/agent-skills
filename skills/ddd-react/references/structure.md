# Folder structure, naming, and environment

How a React app is laid out by bounded context, what every file is called, and where URLs come from.

Organize `src/` by **bounded context** (a feature area), and split each context into four layers: `domain`, `application`, `infrastructure`, and `presentation` — the frontend's name for the `interfaces`/inbound layer.

```
src/
├── ordering/                            // bounded context
│   ├── domain/
│   │   └── model/
│   │       ├── order.entity.ts          // class Order — readonly fields, behaviour
│   │       └── place-order.command.ts   // class PlaceOrderCommand
│   ├── application/
│   │   └── ordering.store.ts            // useOrderingStore (Zustand)
│   ├── infrastructure/
│   │   ├── ordering-api.ts              // class OrderingApi extends BaseApi
│   │   ├── order.resource.ts            // OrderResource (the wire shape)
│   │   └── order.assembler.ts           // OrderAssembler (static)
│   └── presentation/
│       ├── views/                       // routed, smart components
│       │   ├── OrderList.tsx
│       │   └── OrderForm.tsx
│       ├── components/                  // reusable, dumb components
│       │   └── OrderCard.tsx
│       ├── ordering-paths.ts            // every URL this context owns
│       └── ordering-routes.tsx          // its RouteObject[]
├── identity/                            // a second context, same four layers
├── shared/                              // the shared kernel — see shared-kernel.md
├── router.tsx                           // composes the contexts
└── main.tsx
```

Dependencies point inward toward `domain`: `presentation`, `application`, and `infrastructure` depend on `domain`; `domain` depends on nothing — not React, not axios, not the router. Each context owning its routes and its paths keeps the boundary visible in the routing table too.

Entities live in `domain/model/`, and so do commands. Keep them together: a command is part of the domain's vocabulary, not a transport detail.

## The naming convention

**Component files are PascalCase**, matching the component they export — the dominant React convention, and what JSX reads as. Everything else follows the family's rule, where the separator carries meaning:

- **A dot** when the suffix names the kind of building block — `order.entity.ts`, `order.resource.ts`, `order.assembler.ts`, `place-order.command.ts`, `ordering.store.ts`, `authentication.loader.ts`, `identity.interceptor.ts`.
- **A dash** when the name itself is compound — `ordering-api.ts`, `ordering-routes.tsx`, `ordering-paths.ts`, `base-endpoint.ts`.

| Layer | File | Exports |
| --- | --- | --- |
| domain | `order.entity.ts` | `class Order`, `interface OrderAttributes` |
| domain | `place-order.command.ts` | `class PlaceOrderCommand` |
| application | `ordering.store.ts` | `useOrderingStore`, `interface OrderingState` |
| infrastructure | `order.resource.ts` | `interface OrderResource` |
| infrastructure | `order.assembler.ts` | `class OrderAssembler`, static methods |
| infrastructure | `ordering-api.ts` | `class OrderingApi extends BaseApi` |
| infrastructure | `authentication.loader.ts` | `authenticationLoader` |
| infrastructure | `identity.interceptor.ts` | `identityInterceptor` |
| presentation | `ordering-paths.ts` | `orderingPaths` |
| presentation | `ordering-routes.tsx` | `orderingRoutes: RouteObject[]` |
| presentation | `views/OrderList.tsx` | `function OrderList` |
| presentation | `components/OrderCard.tsx` | `function OrderCard` |

Only files containing JSX need `.tsx`; the rest are `.ts`. That is why `ordering-routes.tsx` carries the extension and `ordering-paths.ts` does not.

A store is named after the **context**, not the entity: `useOrderingStore` holds orders and whatever else the context owns. One store per context is the rule; see `state-store.md`.

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

The keys say **which provider** and **which endpoint**: `VITE_PLATFORM_API_URL` is your own backend; a third party gets its own prefix (`VITE_MAPS_API_URL`). That makes it obvious at a glance when a call leaves your system — and those are exactly the calls that need an anti-corruption layer.

In TypeScript, declare them once so `import.meta.env` is typed rather than `any`:

```typescript
// src/vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_PLATFORM_API_URL: string;
    readonly VITE_ORDERS_ENDPOINT_PATH: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
```

That file is what turns a typo in an env key into a compile error instead of an `undefined` baseURL, which axios sends as a **relative** request against your own origin — returning `index.html` rather than anything that names the missing key.

Both env files declare the **same keys**; only the values differ.

> **Secrets.** Everything prefixed `VITE_` is inlined into the bundle and readable by anyone. Fine for a public, rate-limited provider; anything that must stay secret belongs behind your own backend.

## Strategic design on the frontend

- **Bounded contexts** become feature folders. A real app has several — `ordering`, `catalog`, `identity` — each with its own model, gateway, store, views, paths and routes. When one context needs another, it goes through that context's store, never its internals.
- **Ubiquitous language** runs through the names: `Order`, `useOrderingStore`, `OrderingApi`, `PlaceOrderCommand`.
- **The shared kernel** (`shared/`) holds only what every context reuses, and stays small.
- **Assemblers** are the anti-corruption layer: the shape of whatever you integrate with stops at the edge of the context.
