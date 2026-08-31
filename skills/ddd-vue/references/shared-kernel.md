# The shared kernel

The two base classes every bounded context builds on.

The Vue kernel is small on purpose. It is `shared/`, and it holds only what every context genuinely reuses:

```
shared/
├── infrastructure/
│   ├── base-api.js        // BaseApi — one configured Axios instance
│   └── base-endpoint.js   // BaseEndpoint — CRUD over one resource
└── presentation/
    ├── components/        // the app shell, footer, language switcher
    └── views/             // app-wide views: home, about, page-not-found
```

**Copy both files as they are** from `assets/shared-kernel/` — they are boilerplate, and the point is that every project has the same ones:

```bash
cp -R "$SKILL/assets/shared-kernel/" src/shared/    # $SKILL = this skill's directory
```

| File | What it is | Why |
| --- | --- | --- |
| `base-api.js` | `class BaseApi` holding a private, configured Axios instance behind a `get http()` | A context API extends it and composes endpoints on top. The instance is private, so no store or view can reach the transport. |
| `base-endpoint.js` | `class BaseEndpoint` with `getAll`, `getById`, `create`, `update`, `delete` | The repository of the frontend: one instance per resource, constructed with a gateway and a path. |

There is no `application/` layer in the kernel, and that absence is a statement: a store belongs to a bounded context and orchestrates its use cases, so it can never be shared. A kernel that grows a store has started absorbing someone's domain.

There is also no `BaseEntity` and no `BaseAssembler`. In a JavaScript codebase they would buy nothing — there is no compiler to satisfy, and an entity is already just a class with public fields. The contract lives in the JSDoc and in the convention, not in an interface.

## The endpoint returns the response, not entities

This is the one thing to understand before writing anything else.

`BaseEndpoint.getAll()` resolves to a raw `AxiosResponse`. It does **not** return `Order[]`. Turning a response into entities is the assembler's job, and the assembler is called **from the store**:

```javascript
orderingApi.getOrders()                                  // infrastructure: HTTP only
    .then(response => {
        orders.value = OrderAssembler.toEntitiesFromResponse(response);   // application
    });
```

Why draw the line there rather than inside the endpoint: an envelope key, a pagination wrapper, or a status convention can change without touching the transport, and one generic endpoint can then serve every resource in the app. The cost is that a store which forgets to assemble ends up holding raw resources, and nothing stops it — so treat "the store assembles, always" as the rule it is.

## Wiring cross-cutting request handling

`BaseApi` takes its interceptors as a constructor option:

```javascript
new OrderingApi({requestInterceptors: [identityInterceptor]});
```

rather than importing one directly. That keeps `shared/` from depending on a bounded context, which would invert the dependency rule the whole structure exists to enforce. See `cross-cutting.md` for where the interceptor itself lives and how it gets passed in.
