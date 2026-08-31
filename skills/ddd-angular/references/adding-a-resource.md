# Adding a resource, end to end

The order to write the files in, and what to check when you are done.

Use this when the task is "add X to the app" — a new bounded context, or a new aggregate inside one. Work outward from the domain: each step only depends on the ones before it, so nothing is written twice.

## Before writing anything

1. **Name it in the ubiquitous language.** Ask what the domain experts call it. `Order`, not `Purchase` and not `Transaction`. Every file name, class name, route path, and store method comes from this answer.
2. **Decide which bounded context it belongs to.** A new context if it has its own model and language; otherwise a new aggregate inside an existing one. When in doubt, look at whether it would share a store with what is already there.
3. **Learn the wire shape.** Read the actual API response — field names, casing, nulls, whether the collection comes wrapped in an envelope. Guessing here is what produces an assembler that silently maps nothing.

## Scaffold, then model

For a new context, generate the tree instead of typing it:

```bash
python3 scripts/new-context.py --context ordering --entity Order --into src/app
```

That writes all four layers wired together for one CRUD aggregate. Everything below then becomes editing rather than authoring — which is the point, since the naming is the error-prone part.

Copy the shared kernel from `assets/shared-kernel/` first if `src/app/shared/` does not have it yet.

## The nine files, in order

| # | File | What to write |
| --- | --- | --- |
| 1 | `domain/model/order.entity.ts` | The real fields, in the ubiquitous language. Private fields, accessors, one options-object constructor, `implements BaseEntity`. Setters only where the UI changes the value. See `domain-model.md`. |
| 2 | `infrastructure/orders-response.ts` | `OrderResource` and `OrdersResponse`, mirroring the API exactly — its casing, its nulls, its envelope key. |
| 3 | `infrastructure/order-assembler.ts` | The three mappings. Every difference between 1 and 2 is resolved here and nowhere else. |
| 4 | `infrastructure/orders-api-endpoint.ts` | URL from `environment`, plus the assembler. Nothing else. |
| 5 | `infrastructure/ordering-api.ts` | Add one endpoint field and its operations, named in the domain's language. |
| 6 | `application/ordering.store.ts` | Signals, `computed` queries, load/add/update/delete, `formatError`. Stitch related entities here if there are any. See `state-store.md`. |
| 7 | `presentation/views/order-list/` | The routed list view: inject the store, render its signals, dispatch. |
| 8 | `presentation/views/order-form/` | The create/edit view. Builds the entity and hands it to the store. See `forms.md`. |
| 9 | `presentation/ordering.routes.ts` | Three routes, all lazy: list, new, edit. |

Then two edits outside the context:

- **`environments/environment.ts` and `environment.development.ts`** — add `platformProviderOrdersEndpointPath` to **both**.
- **`app.routes.ts`** — mount the context with `loadChildren`, plus a guard if it needs one.

## If the operation is not CRUD

Placing an order, cancelling with a reason, signing in — anything where the body is not a record. Replace steps 1–4 with the command path: a `*.command.ts` in the domain, a `*.request.ts`, a `*-response.ts`, an assembler with `toRequestFromCommand` and `toResourceFromResponse`, and an endpoint extending `ErrorHandlingEnabledBaseType`. See `commands-and-actions.md`. Steps 5, 6, and 9 are unchanged.

## Checklist

Before calling it done:

- [ ] Every name reads in the ubiquitous language — no `Data`, `Info`, `Manager`, or `Helper`.
- [ ] `OrderResource` appears in `infrastructure/` and nowhere else. Grep for it.
- [ ] No `HttpClient` outside an endpoint; no endpoint held by a store.
- [ ] Both `environment` files declare the same keys.
- [ ] The store sets `loading` and clears it in **both** the success and the error branch.
- [ ] Reads use `takeUntilDestroyed(this.destroyRef)`; writes use `retry(2)`.
- [ ] The list view holds no filtering or merging that could be a `computed()` in the store.
- [ ] Every route in the context is lazy-loaded, and the context is mounted with `loadChildren`.
- [ ] Classes, interfaces, and public methods carry JSDoc; no debug `console.log` survives.
- [ ] The form validates for the user and builds a domain object — it does not build a request body.
