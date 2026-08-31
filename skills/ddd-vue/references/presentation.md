# The presentation layer: views, components, and routing

Routed smart views, reusable dumb components, and how each context owns its routes.

The layer has exactly two kinds of single-file component, and the split is the whole design:

- A **view** lives in `presentation/views/` — routed, "smart". It reads the store, dispatches actions, and navigates.
- A **component** lives in `presentation/components/` — reusable, "dumb". It takes data through `defineProps`, reports intent through `defineEmits`, and knows nothing about the store, the gateway, or the router.

```vue
<!-- ordering/presentation/views/order-list.vue -->
<script setup>
/**
 * @component OrderList
 * @description Routed view listing the active orders of the ordering context.
 */
import {onMounted} from 'vue';
import {storeToRefs} from 'pinia';
import {useRouter} from 'vue-router';
import useOrderingStore from '../../application/ordering.store.js';
import OrderCard from '../components/order-card.vue';

const router = useRouter();
const store = useOrderingStore();
const {activeOrders, errors, ordersLoaded} = storeToRefs(store);
const {fetchOrders, cancelOrder} = store;

onMounted(() => {
  if (!ordersLoaded.value) fetchOrders();
});

/**
 * Navigates to the edit form for one order.
 * @param {number} id - Identity of the order to edit.
 * @returns {void}
 */
function navigateToEdit(id) {
  router.push({name: 'ordering-order-edit', params: {id}});
}
</script>

<template>
  <section>
    <h1>Orders</h1>
    <p v-if="!ordersLoaded">Loading…</p>
    <p v-if="errors.length" role="alert">{{ errors.map(error => error.message).join(', ') }}</p>

    <order-card
        v-for="order in activeOrders"
        :key="order.id"
        :order="order"
        @cancel-requested="cancelOrder"
        @edit-requested="navigateToEdit"/>
  </section>
</template>
```

```vue
<!-- ordering/presentation/components/order-card.vue -->
<script setup>
/**
 * @component OrderCard
 * @description Presents one order and reports what the user wants done with it.
 *
 * ### Props
 * | Name    | Type    | Required | Description                  |
 * |---------|---------|----------|------------------------------|
 * | `order` | `Order` | yes      | The order entity to display. |
 *
 * ### Emitted events
 * | Event              | Payload  | Description                          |
 * |--------------------|----------|--------------------------------------|
 * | `cancel-requested` | `number` | Identity of the order to cancel.     |
 * | `edit-requested`   | `number` | Identity of the order to edit.       |
 */
import {toRefs} from 'vue';
import {Order} from '../../domain/model/order.entity.js';

const props = defineProps({order: {type: Order, required: true}});
const emit = defineEmits(['cancel-requested', 'edit-requested']);
const {order} = toRefs(props);
</script>

<template>
  <article>
    <h2>Order #{{ order.id }}</h2>
    <p>{{ order.itemCount() }} items · {{ order.status }}</p>

    <button type="button" @click="emit('edit-requested', order.id)">Edit</button>
    <button v-if="order.isCancellable()" type="button" @click="emit('cancel-requested', order.id)">
      Cancel
    </button>
  </article>
</template>
```

A dumb component **emits, it does not decide**. `OrderCard` never calls the store; it says "the user asked to cancel this id" and the view decides what that means. That is what lets the same card appear in a dashboard, a search result, and a printout.

Note `order.isCancellable()` in the template. The rule lives on the entity (see `domain-model.md`), so the component asks rather than re-deriving — and the same question from three templates gets the same answer.

Two details that keep the split honest:

- **Type the prop with the entity class.** `{type: Order, required: true}` makes Vue warn in development when a raw resource is passed instead of an assembled entity — a cheap check that the anti-corruption layer was not skipped.
- **`toRefs(props)`** so destructuring does not flatten reactivity. Destructuring `props` directly gives a value that never updates.

The view stays thin too: wire the store to the components, handle navigation, stop. A view that filters, merges, or reformats domain data has taken work that belongs to a `computed` in the store or a method on the entity.

## Routing

Each context owns a `*-routes.js` **inside its `presentation/` folder**, exporting an array that lazy-loads every view:

```javascript
// ordering/presentation/ordering-routes.js
const orderList = () => import('./views/order-list.vue');
const orderForm = () => import('./views/order-form.vue');

/**
 * Routes of the ordering bounded context.
 * All paths are relative to the `/ordering` parent route.
 *
 * @type {import('vue-router').RouteRecordRaw[]}
 */
const orderingRoutes = [
    {path: 'orders',           name: 'ordering-orders',      component: orderList, meta: {title: 'Orders'}},
    {path: 'orders/new',       name: 'ordering-order-new',   component: orderForm, meta: {title: 'New Order'}},
    {path: 'orders/:id/edit',  name: 'ordering-order-edit',  component: orderForm, meta: {title: 'Edit Order'}}
];

export default orderingRoutes;
```

**Every route is named, and navigation goes by name** — `router.push({name: 'ordering-order-edit', params: {id}})`, never a hand-built path string. Renaming a URL segment then touches one file instead of every component that linked to it. Prefix the names with the context (`ordering-`) so two contexts can both have a list without colliding.

`meta.title` is read by a global guard to set the document title; see `cross-cutting.md`.

The root `router.js` composes the contexts as children:

```javascript
// router.js
import {createRouter, createWebHistory} from 'vue-router';
import Home from './shared/presentation/views/home.vue';
import orderingRoutes from './ordering/presentation/ordering-routes.js';
import identityRoutes from './identity/presentation/identity-routes.js';

const about = () => import('./shared/presentation/views/about.vue');
const pageNotFound = () => import('./shared/presentation/views/page-not-found.vue');

const routes = [
    {path: '/home',             name: 'home',     component: Home,   meta: {title: 'Home'}},
    {path: '/about',            name: 'about',    component: about,  meta: {title: 'About'}},
    {path: '/ordering',         name: 'ordering', children: orderingRoutes},
    {path: '/identity',         name: 'identity', children: identityRoutes},
    {path: '/',                 redirect: '/home'},
    {path: '/:pathMatch(.*)*',  name: 'not-found', component: pageNotFound, meta: {title: 'Page Not Found'}}
];

const router = createRouter({history: createWebHistory(import.meta.env.BASE_URL), routes});

export default router;
```

Lazy-loading each view keeps the bounded-context boundary visible in the routing table, and the bundles split along it. The catch-all comes last; the sign-in routes stay outside any guard.

## The app shell

`app.vue` renders one thing — the layout — and the layout owns the chrome and the outlet:

```vue
<!-- app.vue -->
<script setup>
import Layout from './shared/presentation/components/layout.vue';
</script>

<template>
  <layout/>
</template>
```

```vue
<!-- shared/presentation/components/layout.vue -->
<script setup>
/**
 * @component Layout
 * @description The app shell — chrome around whatever the router puts in the outlet.
 */
const options = [
  {label: 'Home', to: {name: 'home'}},
  {label: 'Orders', to: {name: 'ordering-orders'}},
  {label: 'About', to: {name: 'about'}}
];
</script>

<template>
  <header>
    <nav>
      <router-link v-for="option in options" :key="option.label" :to="option.to">
        {{ option.label }}
      </router-link>
    </nav>
  </header>
  <router-view/>
  <footer-content/>
</template>
```

Keeping the shell in `shared/presentation/components/` rather than in `app.vue` lets the root component stay empty and the navigation stay one array. The layout is the one place allowed to reach into several contexts at once — it links to them by route name, which is the loosest coupling available.

A real app also puts a component library here (PrimeVue, Vuetify, whatever you use) and a translation pipe in the templates. Keep both in the presentation layer: a store, an entity, an assembler, or a gateway must not import either.
