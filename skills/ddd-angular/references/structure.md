# Folder structure: bounded contexts and four layers

How an Angular app is laid out by bounded context, and how the four layers map onto it.

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
├── shared/                            // the shared kernel (see `shared-kernel.md`)
└── app.routes.ts                      // root router composes the contexts
```

Dependencies point inward toward `domain`: `presentation` and `infrastructure` depend on `domain`; `domain` depends on nothing. Each context owning its own routes (lazy-loaded from the root router) keeps the boundary visible at the routing level too.

## Strategic design on the frontend

- **Bounded contexts** become feature folders (or, in an Nx workspace, separate libraries) — a real app has several (e.g., `ordering`, `identity`, `catalog`), each with its own model, API, store, views, and lazy-loaded routes. When one context needs another — say `ordering` needs the signed-in user from `identity` — it consumes that context's store or service, not its internals, so the boundary holds.
- **Ubiquitous language** runs through the names: `Order`, `OrderStore`, `OrderingApi`, `SignInCommand` — the same terms the backend and the domain experts use.
- **The shared kernel** (`shared/`, see `shared-kernel.md`) holds what every context reuses — base classes, the app shell, and app-wide views — and stays small; most things belong to one context.
- **Assemblers** are the anti-corruption layer: they protect your model from the shape of whatever you integrate with (a backend, a third-party API).

A real app also leans on plumbing that isn't domain modeling: a component library and an i18n pipe in the views (e.g. Angular Material and ngx-translate), and cross-cutting wiring in infrastructure (route guards, HTTP interceptors). Keep it where it belongs — out of the domain and the stores — and don't mistake it for the model.
