# Adding a resource, end to end

The order to write the files in, and what to check when you are done.

Use this when the task is "add X to the app" — a new bounded context, or a new aggregate inside one. Work outward from the domain: each step depends only on the ones before it, so nothing is written twice.

## Before writing anything

1. **Name it in the ubiquitous language.** Ask what the domain experts call it. `Order`, not `Purchase` and not `Transaction`. Every file name, class name, route name, and store action comes from this answer.
2. **Decide which bounded context it belongs to.** A new context if it has its own model and language; otherwise a new aggregate inside an existing one. When in doubt, ask whether it would share a store with what is already there.
3. **Learn the wire shape.** Read the actual API response — field names, casing, nulls, whether the collection comes wrapped in an envelope. Guessing here produces an assembler that silently maps nothing.

## Scaffold, then model

For a new context, generate the tree instead of typing it:

```bash
SKILL=.claude/skills/ddd-vue       # wherever this skill was installed
python3 "$SKILL/scripts/new-context.py" --context ordering --entity Order --into src
```

Run it from the root of the app: `--into` is resolved against the current directory. That writes all four layers wired together for one CRUD aggregate, so everything below becomes editing rather than authoring — which is the point, since the naming is the error-prone part.

Copy the shared kernel first if `src/shared/` does not have it yet — `cp -R "$SKILL/assets/shared-kernel/" src/shared/`. See `shared-kernel.md`.

## The seven files, in order

| # | File | What to write |
| --- | --- | --- |
| 1 | `domain/model/order.entity.js` | The real fields, in the ubiquitous language. Public fields, one options-object constructor with defaults, nested entities hydrated. **Add the behaviour** — any rule that reads only off these fields. See `domain-model.md`. |
| 2 | `infrastructure/order.assembler.js` | `toEntityFromResource` and `toEntitiesFromResponse`. Every difference between the wire and step 1 is resolved here and nowhere else. |
| 3 | `infrastructure/ordering-api.js` | One `BaseEndpoint` field per aggregate, and operations named in the domain's language. Path from `import.meta.env`. |
| 4 | `application/ordering.store.js` | Refs, computeds, actions. The store calls the assembler — the gateway hands back a raw response. See `state-store.md`. |
| 5 | `presentation/views/order-list.vue` | The routed list view: read the store, render, dispatch. |
| 6 | `presentation/views/order-form.vue` | The create/edit view. Builds the entity and hands it to the store. See `forms.md`. |
| 7 | `presentation/ordering-routes.js` | Three named routes, all lazy: list, new, edit. |

Then two edits outside the context:

- **`.env.development` and `.env.production`** — add `VITE_ORDERS_ENDPOINT_PATH` to **both**.
- **`router.js`** — mount the context as `children` of its parent path, plus a guard if it needs one.

## If the operation is not CRUD

Placing an order, cancelling with a reason, signing in — anything where the body is not a record. Replace steps 1–3 with the command path: a `*.command.js` in `domain/model/`, a `*.resource.js`, an assembler with `toResourceFromResponse`, and one more operation on the gateway. See `commands-and-actions.md`. Steps 4 and 7 are unchanged.

## Checklist

Before calling it done:

- [ ] Every name reads in the ubiquitous language — no `Data`, `Info`, `Manager`, or `Helper`.
- [ ] The entity has **behaviour**, not just fields. Any rule repeated in two templates belongs on it.
- [ ] The domain layer imports nothing from Vue, axios, or the router.
- [ ] No axios outside `infrastructure/`; no endpoint held by a store.
- [ ] The store calls the assembler on every read and every write — no `response.data` assigned straight into a ref.
- [ ] Both `.env` files declare the same keys.
- [ ] Route params are coerced with `Number(...)` before comparing against an entity id.
- [ ] Views use `storeToRefs` for state and plain destructuring for actions.
- [ ] Every route in the context is named and lazy-loaded, and navigation goes by name.
- [ ] Classes, exported functions and store state carry JSDoc; no debug `console.log` survives.
- [ ] The form builds a domain object — it does not build a request body.
