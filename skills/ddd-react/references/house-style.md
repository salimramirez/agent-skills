# House style

The conventions that make this code recognizable, beyond where the files sit.

## Types are the contract, JSDoc is the reason

TypeScript states the shape, so a comment repeating it is noise. Write a doc block when it says something the signature cannot: why a decision was made, what a value means in the domain, what a caller must not do.

```typescript
/**
 * Builds the collection from a response, tolerating both wire shapes.
 *
 * A bare array and an envelope keyed by the resource name both occur in the wild.
 * A non-200 yields an empty collection rather than a throw: the store already
 * records the error, and a view rendering nothing beats one that crashes.
 */
static toEntitiesFromResponse(response: AxiosResponse<…>): Order[] { … }
```

Document every exported class, every exported function, and the store's state interface. Skip the ones where the name and type already say everything — `getOrders()` returning `Promise<AxiosResponse>` needs nothing.

Never `any`. Where a shape is genuinely unknown, `unknown` plus a narrowing at the boundary is the honest version, and the boundary is the assembler.

## Prefer `type` imports

`import type {OrderResource} from …` for anything that exists only as a type — an interface, a type alias. With `verbatimModuleSyntax`, on by default in Vite's template, importing one *without* the modifier is `TS1484: 'OrderResource' is a type and must be imported using a type-only import`. A class is a value as well as a type, so `import {Order}` stays correct; the modifier is for the shapes that vanish at runtime.

## Order members predictably

In a store: state fields first, then the actions, all inside one `create()` call, with the shape declared as an exported interface above. Reading it top to bottom should read as "what it holds, then what it does".

In a component: hooks first (`useNavigate`, store selectors, `useState`), then effects, then handlers, then the JSX. Anything computed from props or state goes between the hooks and the return, never inside the JSX.

## Keep the layers honest

Each of these is a smell with a name:

- **No axios outside `infrastructure/`.** Only a gateway touches it. A store calls its gateway; a component calls its store.
- **No raw resource above `infrastructure/`.** If a component reads `order.customer_id`, the assembler was skipped — and in TypeScript that is a compile error, so it means someone reached for a cast.
- **No business or coordination logic in a component.** Deciding what to load next, stitching two collections, formatting an error — that is the store's job.
- **The domain layer imports nothing from React, axios or the router.** An entity that imports `useState` has stopped being a domain object. This is the easiest rule to break and the most expensive to unwind.
- **The store imports nothing from React either.** Zustand makes this possible and it is worth protecting: it is what lets a loader or an interceptor read state with `.getState()`, and what lets the application layer be tested without rendering.
- **One store per bounded context**, not one per entity and not one for the app.

## Never mutate

React compares by reference, so mutation is invisible to it. Every state update replaces:

```typescript
set({orders: [...get().orders, created]});                                   // yes
set({orders: get().orders.map(o => o.id === updated.id ? updated : o)});     // yes
get().orders.push(created);                                                  // renders nothing
```

`readonly` on entity fields and `readonly T[]` on collections make the wrong version fail to compile rather than fail silently. This is the single most common source of "the data is there but the screen is stale".

## Comparisons and identity

Entities are compared by `id`, never by object identity — an entity that has been through a write is a different instance carrying the same identity.

Watch the type: a route parameter arrives as a **string**, so coerce before comparing (`Number(id)`). A silent `'3' !== 3` is the most common reason an edit form opens empty, and TypeScript will not catch it because `useParams()` gives you `string | undefined` and comparing it to a number is a valid question to ask.

A new entity is built with `id: null`; the backend assigns the real one and the store keeps what came back.
