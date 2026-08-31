# Adding a resource, end to end

The order to write the files in, and what to check when you are done.

Use this when the task is "add X to the app" — a new bounded context, or a new aggregate inside one. Work outward from the domain: each step depends only on the ones before it, so nothing is written twice.

## Before writing anything

1. **Name it in the ubiquitous language.** Ask what the domain experts call it. `Order`, not `Purchase` and not `Transaction`. Every file name, class name, path builder and store action comes from this answer.
2. **Decide which bounded context it belongs to.** A new context if it has its own model and language; otherwise a new aggregate inside an existing one. When in doubt, ask whether it would share a store with what is already there.
3. **Learn the wire shape.** Read the actual API response — field names, casing, nulls, whether the collection comes wrapped in an envelope. Guessing here produces an assembler that maps nothing, and TypeScript will happily agree with your guess.

## Scaffold, then model

For a new context, generate the tree instead of typing it:

```bash
SKILL=.claude/skills/ddd-react       # wherever this skill was installed
python3 "$SKILL/scripts/new-context.py" --context ordering --entity Order --into src
```

Run it from the root of the app: `--into` is resolved against the current directory. That writes all four layers wired together for one CRUD aggregate, so everything below becomes editing rather than authoring — which is the point, since the naming is the error-prone part.

Copy the shared kernel first if `src/shared/` does not have it yet — `cp -R "$SKILL/assets/shared-kernel/" src/shared/`. See `shared-kernel.md`.

## The nine files, in order

| # | File | What to write |
| --- | --- | --- |
| 1 | `domain/model/order.entity.ts` | The real fields, in the ubiquitous language. `readonly` fields, one options-object constructor with defaults, nested entities hydrated. **Add the behaviour** — any rule that reads only off these fields. See `domain-model.md`. |
| 2 | `infrastructure/order.resource.ts` | The wire shape as an interface, exactly as the API sends it. |
| 3 | `infrastructure/order.assembler.ts` | The three mappings. Every difference between 1 and 2 is resolved here and nowhere else. |
| 4 | `infrastructure/ordering-api.ts` | One `BaseEndpoint` field per aggregate, and operations named in the domain's language. Path from `import.meta.env`. |
| 5 | `application/ordering.store.ts` | The state interface, then `create()`. The store calls the assembler — the gateway hands back a raw response. See `state-store.md`. |
| 6 | `presentation/ordering-paths.ts` | Every URL this context owns. Nothing else writes one. |
| 7 | `presentation/views/OrderList.tsx` | The routed list view: select from the store, render, dispatch. |
| 8 | `presentation/views/OrderForm.tsx` | The create/edit view. Builds the entity and hands it to the store. See `forms.md`. |
| 9 | `presentation/ordering-routes.tsx` | Three routes with relative paths. |

Then three edits outside the context:

- **`.env.development` and `.env.production`** — add `VITE_ORDERS_ENDPOINT_PATH` to **both**.
- **`src/vite-env.d.ts`** — declare the new key on `ImportMetaEnv`, or `import.meta.env` stays untyped for it.
- **`router.tsx`** — mount the context as `children`, plus a loader if it needs one.

## If the operation is not CRUD

Placing an order, cancelling with a reason, signing in — anything where the body is not a record. Replace steps 1–4 with the command path: a `*.command.ts` in `domain/model/`, a `*.resource.ts`, an assembler with `toRequestFromCommand` and `toResourceFromResponse`, and one more operation on the gateway. See `commands-and-actions.md`. Steps 5, 6 and 9 are unchanged.

## Checklist

Before calling it done:

- [ ] Every name reads in the ubiquitous language — no `Data`, `Info`, `Manager`, or `Helper`.
- [ ] The entity has **behaviour**, not just fields, and every field is `readonly`.
- [ ] Nothing mutates: every store update replaces the array or the entity.
- [ ] The domain layer imports nothing from React, axios or the router — and neither does the store.
- [ ] No axios outside `infrastructure/`; no endpoint held by a store.
- [ ] The store calls the assembler on every read and write. No `response.data` assigned into state.
- [ ] Both `.env` files declare the same keys, and `vite-env.d.ts` knows about them.
- [ ] Route params are coerced with `Number(...)` before comparing against an entity id.
- [ ] Components select one slice per `useStore` call, and no selector builds a new object.
- [ ] Every URL comes from the context's `*-paths.ts`; no path string is typed into `navigate()`.
- [ ] Exported classes and functions carry a doc block that says *why*, not what the type says.
- [ ] `npm run build` passes — not just the editor. It runs `tsc -b`, which is stricter.
