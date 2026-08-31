# The shared kernel

The base classes and app-wide pieces every bounded context reuses.

The `shared/` folder is the **shared kernel** — what genuinely belongs to every context. Unlike on the backend, it spans all four layers, including UI:

```
shared/
├── domain/model/
│   └── base-entity.ts                      // BaseEntity — the { id } every entity carries
├── infrastructure/
│   ├── base-response.ts                    // BaseResource / BaseResponse (DTO contracts)
│   ├── base-assembler.ts                   // BaseAssembler<Entity, Resource, Response>
│   ├── error-handling-enabled-base-type.ts // ErrorHandlingEnabledBaseType — handleError
│   ├── base-api-endpoint.ts                // BaseApiEndpoint — generic CRUD
│   └── base-api.ts                         // BaseApi — base for a context's API
└── presentation/
    ├── components/                         // Layout (app shell), footer, BaseForm
    └── views/                              // app-wide views: home, about, page-not-found
```

**Copy these seven files as they are** from `assets/shared-kernel/` — they are boilerplate, and the whole point is that every project has the same ones. What each contributes:

| File | What it is | Why |
| --- | --- | --- |
| `base-entity.ts` | `interface BaseEntity { id: number }` | The one thing every entity shares, so the generic infrastructure can work with any of them. Entities `implements BaseEntity`. |
| `base-response.ts` | `interface BaseResource { id: number }`, `interface BaseResponse {}` | Names the two wire shapes: the item and the envelope. |
| `base-assembler.ts` | `interface BaseAssembler<TEntity, TResource, TResponse>` | The anti-corruption contract — three methods, both directions. |
| `error-handling-enabled-base-type.ts` | `abstract class` with `handleError(operation)` | Turns an `HttpErrorResponse` into one labelled `Error` so transport details never reach the application layer. |
| `base-api-endpoint.ts` | `abstract class BaseApiEndpoint<…>` | The repository: `getAll`, `getById`, `create`, `update`, `delete`, every result through the assembler. Extends `ErrorHandlingEnabledBaseType`. |
| `base-api.ts` | `abstract class BaseApi` | A marker a context API extends. Empty on purpose; it states the role and gives the family a name. |
| `base-form.ts` | `class BaseForm` | `isInvalidControl` and `errorMessagesForControl`, so form templates stop repeating `touched && hasError(...)`. |

Two notes on `BaseApiEndpoint` worth knowing before you subclass it:

- **`getAll` accepts both wire shapes** — a bare array or an envelope. A mock server that returns `[…]` and a real backend that returns `{ orders: […] }` both work without touching the store.
- **Errors arrive as `Error`, not `HttpErrorResponse`.** The store reads `error.message`; see the `formatError` helper in `state-store.md`.

The presentation half of the kernel is real UI, and it belongs here because every context renders inside it: a **`Layout`** shell (toolbar, nav, `<router-outlet/>`, footer), app-wide **views** (`home`, `about`, `page-not-found`), cross-cutting components, and **`BaseForm`**. It is UI rather than domain, but it is *shared* UI, so it lives here rather than in any one context.

Keep the kernel small: base classes, the app shell, a few app-wide views. Anything that belongs to one domain belongs in that context — a shared folder that grows an `order-helpers.ts` has stopped being a kernel.
