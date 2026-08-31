<script setup>
/**
 * @component __Entity__List
 * @description Routed view listing the __entities__ of the __context__ context.
 *
 * A view is the smart component: it reads store state, dispatches actions and
 * navigates. It holds no business rule and makes no HTTP call.
 */
import {onMounted} from 'vue';
import {storeToRefs} from 'pinia';
import {useRouter} from 'vue-router';
import use__Context__Store from '../../application/__context__.store.js';

const router = useRouter();
const store = use__Context__Store();
const {__entities__, errors, __entities__Loaded} = storeToRefs(store);
const {fetch__Entities__, delete__Entity__} = store;

onMounted(() => {
  if (!__entities__Loaded.value) fetch__Entities__();
});

/**
 * Navigates to the creation form.
 * @returns {void}
 */
function navigateToNew() {
  router.push({name: '__context__-__entity-kebab__-new'});
}

/**
 * Navigates to the edit form for one __entity__.
 * @param {number} id - Identity of the __entity__ to edit.
 * @returns {void}
 */
function navigateToEdit(id) {
  router.push({name: '__context__-__entity-kebab__-edit', params: {id}});
}
</script>

<template>
  <section>
    <h1>__Entities__</h1>

    <p v-if="!__entities__Loaded">Loading…</p>
    <p v-if="errors.length" role="alert">{{ errors.map(error => error.message).join(', ') }}</p>

    <ul>
      <li v-for="__entity__ in __entities__" :key="__entity__.id">
        <span>{{ __entity__.name }}</span>
        <button type="button" @click="navigateToEdit(__entity__.id)">Edit</button>
        <button type="button" @click="delete__Entity__(__entity__)">Delete</button>
      </li>
    </ul>

    <button type="button" @click="navigateToNew">New __Entity__</button>
  </section>
</template>
