# House style

The conventions that make this code recognizable, beyond where the files sit.

## JSDoc is the type system

There is no TypeScript here, so a JSDoc block is not decoration — it is the only place the shape of a thing is written down. An editor reads it, and so does the next person.

The rule: **document every class, every exported function, and every piece of store state.** Use `@param` and `@returns` when the name alone does not say it, `@type` on refs and fields, `@remarks` for the reason behind a decision, and `@see {@link Other}` to point at the related piece.

```javascript
/**
 * An order placed by a customer in the ordering context.
 *
 * @remarks
 * The backend owns the invariants — a total is recomputed server-side on every
 * write — so nothing here should be trusted as authoritative.
 *
 * @see {@link PlaceOrderCommand} for the non-CRUD path that creates one.
 * @class Order
 */
export class Order {
    /**
     * @param {Object} params - Entity attributes.
     * @param {?number} [params.id=null] - Identity; null until the backend assigns one.
     * @param {OrderLine[]} [params.lines=[]] - What was ordered.
     */
    constructor({id = null, lines = []} = {}) {
        /** @type {?number} Identity; null until the backend assigns one. */
        this.id = id;
        /** @type {OrderLine[]} What was ordered. */
        this.lines = lines;
    }
}
```

Two annotations carry real weight in a Vue codebase and are worth writing out in full:

```javascript
/** @type {import('vue').Ref<Order[]>} Loaded orders. */
const orders = ref([]);

/** @type {import('vue').ComputedRef<number>} How many orders are loaded. */
const orderCount = computed(() => orders.value.length);
```

Write the comment for someone who does not know the domain. `@param {number} id - The id` is noise; `@param {number} id - Identity of the order to cancel` is not.

## Import with the extension

Every relative import carries its `.js` or `.vue`: `import {Order} from '../domain/model/order.entity.js'`. Vite resolves extensionless paths in dev and then surprises you at build time; writing them out costs four characters and never surprises anyone.

## Order members predictably

In a store: state refs first, each with its `@type`, then computeds, then actions, then the returned object. Reading it top to bottom should read as "what it holds, what it derives, what it does".

In a `<script setup>`: imports, then composables (`useRouter`, `useI18n`, the store), then reactive state, then functions. The template goes below, styles last.

## Keep the layers honest

Each of these is a smell with a name:

- **No axios outside `infrastructure/`.** Only a gateway touches it. A store calls its context API; a view calls its store.
- **No raw resource in a view.** If a template reads `order.customer_id`, the assembler was skipped.
- **No business or coordination logic in a view.** Deciding what to load next, stitching two collections, formatting an error — that is the store's job. Logic in a component is the frontend's fat controller.
- **The domain layer imports nothing from Vue.** An entity that imports `ref` has stopped being a domain object. This is the easiest rule to break and the most expensive to unwind.
- **No leftover `console.log`.** Debug output that ships tells readers the file was never finished.
- **One store per bounded context**, not one per entity and not one for the app.

## Comparisons and identity

Entities are compared by `id`, never by object identity — an entity that has been through a write is a different instance carrying the same identity. `orders.value.find(order => order.id === id)` is the idiom.

Watch the type: a route parameter arrives as a **string**, so coerce before comparing (`Number(route.params.id)`). A silent `'3' !== 3` is the single most common reason an edit form opens empty.

A new entity is built with `id: null`; the backend assigns the real one and the store keeps what came back.
