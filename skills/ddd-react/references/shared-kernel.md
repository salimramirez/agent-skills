# The shared kernel

The two base classes every bounded context builds on.

The React kernel is small on purpose. It is `shared/`, and it holds only what every context genuinely reuses:

```
shared/
├── infrastructure/
│   ├── base-api.ts        // BaseApi — one configured Axios instance
│   └── base-endpoint.ts   // BaseEndpoint<TResource> — CRUD over one resource
└── presentation/
    ├── components/        // the app shell, footer
    └── views/             // app-wide views: home, about, not-found
```

**Copy both files as they are** from `assets/shared-kernel/` — they are boilerplate, and the point is that every project has the same ones:

```bash
cp -R "$SKILL/assets/shared-kernel/" src/shared/    # $SKILL = this skill's directory
```

| File | What it is | Why |
| --- | --- | --- |
| `base-api.ts` | `abstract class BaseApi` holding a private, configured Axios instance behind a `protected get http()` | A context API extends it and composes endpoints on top. The instance is private, so no store or component can reach the transport. |
| `base-endpoint.ts` | `class BaseEndpoint<TResource>` with `getAll`, `getById`, `create`, `update`, `delete` | The repository of the frontend: one instance per resource, constructed with an Axios instance and a path. |

There is no `application/` layer in the kernel, and that absence is a statement: a store belongs to a bounded context and orchestrates its use cases, so it can never be shared. A kernel that grows a store has started absorbing someone's domain.

There is no `BaseEntity` and no `BaseAssembler` either. An entity is already a class with `readonly` fields, and an assembler is a pair of static functions — a base class or interface for either would add a constraint without adding a guarantee.

## The endpoint returns the response, not entities

This is the one thing to understand before writing anything else.

`BaseEndpoint.getAll()` resolves to a raw `AxiosResponse`. It does **not** return `Order[]`. Turning a response into entities is the assembler's job, and the assembler is called **from the store**:

```typescript
const response = await orderingApi.getOrders();                      // infrastructure: HTTP only
set({orders: OrderAssembler.toEntitiesFromResponse(response)});      // application
```

Why draw the line there rather than inside the endpoint: an envelope key, a pagination wrapper, or a status convention can change without touching the transport, and one generic endpoint can then serve every resource in the app. The cost is that a store which forgets to assemble ends up holding raw resources — and unlike in JavaScript, TypeScript catches that, because `Order[]` and `OrderResource[]` are not the same type.

## Wiring cross-cutting request handling

`BaseApi` takes its interceptors as a constructor option:

```typescript
new OrderingApi({requestInterceptors: [identityInterceptor]});
```

rather than importing one directly. That keeps `shared/` from depending on a bounded context, which would invert the dependency rule the whole structure exists to enforce. See `cross-cutting.md` for where the interceptor itself lives.

## One TypeScript detail worth knowing before you edit these

Vite's React + TypeScript template enables **`erasableSyntaxOnly`**, which rejects any syntax that emits JavaScript rather than being stripped. That rules out **constructor parameter properties**:

```typescript
constructor(private readonly http: AxiosInstance) {}     // TS1294 in this template
```

So the kernel declares its fields and assigns them in the constructor body. It reads as three more lines and it is the reason for them. The same applies to `enum` and namespaces — prefer a union type (`OrderStatus` in `domain-model.md`) over an enum.
