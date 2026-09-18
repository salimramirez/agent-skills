# Forms and writes

Building an entity from a form for CRUD, and dispatching a command for everything else.

A form gathers and validates input as **UX** — fast feedback while typing. The server validates again and stays the authority; a `required` attribute is a courtesy to the user, not a rule of the domain.

## One view for create and edit

The presence of an `id` route parameter decides which. Both routes load the same view, so there is one form to maintain:

```vue
<!-- ordering/presentation/views/order-form.vue -->
<script setup>
/**
 * @component OrderForm
 * @description Routed view that creates or edits one order.
 */
import {computed, onMounted, reactive} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import useOrderingStore from '../../application/ordering.store.js';
import {Order} from '../../domain/model/order.entity.js';

const route = useRoute();
const router = useRouter();
const store = useOrderingStore();
const {addOrder, updateOrder} = store;

const form = reactive({customerId: null, deliveryAddress: ''});
const isEdit = computed(() => route.params.id !== undefined);
const id = computed(() => Number(route.params.id));

onMounted(() => {
  if (!isEdit.value) return;
  const order = store.getOrderById(id.value);
  if (!order) {
    navigateBack();
    return;
  }
  form.customerId = order.customerId;
  form.deliveryAddress = order.deliveryAddress;
});

/**
 * Builds the order from the form and sends it through the store.
 * @returns {void}
 */
function saveOrder() {
  const order = new Order({
    id: isEdit.value ? id.value : null,
    customerId: form.customerId,
    deliveryAddress: form.deliveryAddress
  });
  if (isEdit.value) updateOrder(order);
  else addOrder(order);
  navigateBack();
}

/**
 * Returns to the list.
 * @returns {void}
 */
function navigateBack() {
  router.push({name: 'ordering-orders'});
}
</script>

<template>
  <section>
    <h1>{{ isEdit ? 'Edit Order' : 'New Order' }}</h1>

    <form @submit.prevent="saveOrder">
      <label for="deliveryAddress">Delivery address</label>
      <input id="deliveryAddress" v-model="form.deliveryAddress" maxlength="160" required type="text"/>

      <button type="submit">{{ isEdit ? 'Update' : 'Create' }}</button>
      <button type="button" @click="navigateBack">Cancel</button>
    </form>
  </section>
</template>
```

The form does exactly three things: collect, validate for the user, and **build a domain object**. It does not talk to the gateway, and it does not shape a request body — `new Order({...})` is the boundary, and the assembler downstream decides what the wire sees.

Four details that matter more than they look:

**`reactive({...})` for the form, not one `ref` per field.** One object to reset, one object to patch, and `v-model="form.field"` reads plainly.

**Convert the route parameter once.** A route param arrives as a string, and passing it through unconverted gives an entity whose id never matches anything in the store — the next update silently creates a duplicate. It is also typed `string | string[]`, since a repeatable param arrives as an array, so handing `route.params.id` straight to the store is a type error as well. One `computed` does the conversion, and everything after it works with a number: `id: null` on create, `id.value` on edit.

**The form holds plain values, not the entity.** Binding `v-model` straight onto an entity instance means a half-typed address is already in the store's copy — and an abandoned edit leaves it there. Build the entity at submit time instead.

**A deep link can arrive before the store has loaded.** `getOrderById` returns `undefined` and the guard above navigates back. If the screen should survive it, watch the store's collection and patch the form when it arrives, rather than blocking the route:

```javascript
watch(() => store.getOrderById(id.value), order => {
  if (order) Object.assign(form, {customerId: order.customerId, deliveryAddress: order.deliveryAddress});
}, {immediate: true});
```

## Validation messages

Native constraints (`required`, `maxlength`, `type="email"`) cover most of it and cost nothing. When a rule is a **domain** rule, put it on the entity and ask it, so the form and the rest of the app agree:

```javascript
const canSubmit = computed(() => form.deliveryAddress.trim().length > 0);
```

A rule that only the form knows will drift from the one the backend enforces. A rule that lives on the entity is asked the same way everywhere.

## The command path

For a **non-CRUD intent**, build a command instead and pass it to the store. Nothing else about the view changes:

```javascript
function placeOrder() {
  store.placeOrder(new PlaceOrderCommand({
    customerId: form.customerId,
    lines: cart.lines,
    deliveryAddress: form.deliveryAddress
  }), router);
}
```

The store sends it through the gateway and the assembler from `commands-and-actions.md`, and the `router` goes along because the outcome decides where the user lands.

Either way the division holds: validation feedback stays in the form, the shape of the write (entity or command) stays in the domain, coordination stays in the store, and navigation stays with the view that dispatched.
