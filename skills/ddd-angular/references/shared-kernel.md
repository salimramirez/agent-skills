# The shared kernel

The base classes and app-wide pieces every bounded context reuses.

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
