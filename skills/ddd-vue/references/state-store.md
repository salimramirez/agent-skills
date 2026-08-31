# The application layer: the Pinia store

The store that holds a context's state and orchestrates its use cases.

One store per bounded context, named after the context: `useOrderingStore`, not `useOrderStore` and not `useAppStore`. It fills the role command and query handlers play on the backend — it talks to the context gateway, calls the assembler, and keeps coordination out of the views.

Use the **setup form** of `defineStore`: refs for state, computeds for derivations, functions for actions, and one object returned at the end. It reads like the composition API everything else in the app is written in.

```javascript
// ordering/application/ordering.store.js
import {defineStore} from 'pinia';
import {computed, ref} from 'vue';
import {OrderingApi} from '../infrastructure/ordering-api.js';
import {OrderAssembler} from '../infrastructure/order.assembler.js';
import {MenuItemAssembler} from '../infrastructure/menu-item.assembler.js';

const orderingApi = new OrderingApi();

/**
 * State and use cases of the ordering bounded context.
 *
 * @returns {Object} State and actions exposed to the presentation layer.
 */
const useOrderingStore = defineStore('ordering', () => {
    /** @type {import('vue').Ref<Order[]>} Loaded orders. */
    const orders = ref([]);
    /** @type {import('vue').Ref<MenuItem[]>} Loaded menu items. */
    const menuItems = ref([]);
    /** @type {import('vue').Ref<Array<Error>>} Errors from failed calls, newest last. */
    const errors = ref([]);
    /** @type {import('vue').Ref<boolean>} Whether orders have been fetched at least once. */
    const ordersLoaded = ref(false);

    /** @type {import('vue').ComputedRef<Order[]>} Orders still in flight. */
    const activeOrders = computed(() =>
        orders.value.filter(order => order.status !== 'DELIVERED' && order.status !== 'CANCELLED'));
    /** @type {import('vue').ComputedRef<number>} How many orders are loaded. */
    const orderCount = computed(() => orders.value.length);

    /**
     * Loads every order from the API.
     * @returns {void}
     */
    function fetchOrders() {
        orderingApi.getOrders()
            .then(response => {
                orders.value = OrderAssembler.toEntitiesFromResponse(response);
                ordersLoaded.value = true;
            })
            .catch(error => errors.value.push(error));
    }

    /**
     * Finds one loaded order by identity.
     *
     * @param {number|string} id - Identity to look up; a route param arrives as a string.
     * @returns {?Order} The order, or undefined while it is absent.
     */
    function getOrderById(id) {
        const numericId = Number(id);
        return orders.value.find(order => order.id === numericId);
    }

    /**
     * Creates an order and adds it to the collection.
     * @param {Order} order - Order built by the form, with `id: null`.
     * @returns {void}
     */
    function addOrder(order) {
        orderingApi.createOrder(order)
            .then(response => orders.value.push(OrderAssembler.toEntityFromResource(response.data)))
            .catch(error => errors.value.push(error));
    }

    // updateOrder, deleteOrder and cancelOrder have the same shape: call the
    // gateway, assemble what comes back, update the ref, push any error.

    return {
        orders, menuItems, errors, ordersLoaded,
        activeOrders, orderCount,
        fetchOrders, getOrderById, addOrder
    };
});

export default useOrderingStore;
```

## What each convention is for

**The gateway is instantiated once, at module scope.** `const orderingApi = new OrderingApi()` outside `defineStore` gives one Axios instance for the app rather than one per store activation.

**State is `ref`, derivations are `computed`.** `activeOrders` and `orderCount` are never stored — a second ref holding the same data in another shape is the frontend's version of a denormalized column that drifts.

**The store is the only caller of an assembler.** The endpoint returns a raw response (see `shared-kernel.md`); this is where it becomes domain objects. A store that assigns `response.data` straight into a ref has skipped the anti-corruption layer, and raw resources will surface in a template later.

**`errors` is an array, not a message.** Failures accumulate rather than overwrite, so a view can show all of them and a second failure never hides the first. Clear it when an operation succeeds if the screen should recover.

**`xLoaded` flags rather than a single `loading`.** They answer "has this ever been fetched?", which is the question a view actually asks before deciding to fetch — and it is what makes navigating back to a list not refetch it. For per-operation spinners, add a `saving` ref alongside; the two answer different questions.

**Coerce route parameters.** `Number(id)` in `getOrderById` is not defensive noise: a route param is a string, and `'3' === 3` is false. This is the most common reason an edit form opens empty.

## Reading a store from a view

Pinia unwraps state when you destructure actions, but **not** when you destructure state — that would break reactivity. Use `storeToRefs` for state and plain destructuring for actions:

```javascript
const store = useOrderingStore();
const {orders, errors, ordersLoaded} = storeToRefs(store);   // stays reactive
const {fetchOrders, deleteOrder} = store;                    // functions, no refs needed
```

Getting this backwards produces a view that renders once and never updates again, with no error anywhere.

## Cross-entity coordination

When an order needs its menu items resolved for display, that stitching belongs here — after the load, and after each write so a newly created order is stitched too:

```javascript
function fetchOrders() {
    orderingApi.getOrders()
        .then(response => {
            orders.value = OrderAssembler.toEntitiesFromResponse(response);
            orders.value.forEach(order => order.lines.forEach(line => {
                line.menuItem = menuItems.value.find(item => item.id === line.menuItemId) ?? null;
            }));
            ordersLoaded.value = true;
        })
        .catch(error => errors.value.push(error));
}
```

Load order matters: menu items before orders. Keep it out of the views — that is the whole reason the application layer exists on the client.

## The light variant, without Pinia

A small app, or a single read-only context, can hold state in a plain `reactive()` object and skip Pinia entirely:

```javascript
// catalog/application/catalog.store.js
import {reactive} from 'vue';
import {CatalogApi} from '../infrastructure/catalog-api.js';
import {MenuItemAssembler} from '../infrastructure/menu-item.assembler.js';

const catalogApi = new CatalogApi();

/**
 * State and use cases of the catalog bounded context.
 *
 * @type {Object}
 */
export const catalogStore = reactive({
    /** @type {MenuItem[]} The menu as last loaded. */
    menuItems: [],
    /** @type {Array<Error>} Errors from failed calls. */
    errors: [],

    /**
     * Loads the menu, once.
     * @returns {void}
     */
    loadMenuItems() {
        if (this.menuItems.length > 0) return;
        catalogApi.getMenuItems()
            .then(response => {
                this.menuItems = MenuItemAssembler.toEntitiesFromResponse(response);
            })
            .catch(error => this.errors.push(error));
    }
});
```

Same architecture: the store still owns state, still calls the assembler, still keeps views thin. What it gives up is devtools, SSR-safe instantiation, and the discipline of a named store id. Start here if the app has one context; move to Pinia when a second store appears, because two `reactive()` singletons importing each other is where this stops scaling.
