<script setup>
/**
 * @component __Entity__Form
 * @description Routed view that creates or edits one __entity__.
 *
 * One view serves both routes -- the presence of an `id` parameter decides which.
 * It collects input, builds a {@link __Entity__}, and hands it to the store. The
 * backend validates again and stays the authority.
 */
import {computed, onMounted, reactive} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import use__Context__Store from '../../application/__context__.store.js';
import {__Entity__} from '../../domain/model/__entity-kebab__.entity.js';

const route = useRoute();
const router = useRouter();
const store = use__Context__Store();
const {add__Entity__, update__Entity__} = store;

const form = reactive({name: ''});
const isEdit = computed(() => route.params.id !== undefined);
const id = computed(() => Number(route.params.id));

onMounted(() => {
  if (!isEdit.value) return;
  const __entity__ = store.get__Entity__ById(id.value);
  if (__entity__) form.name = __entity__.name;
  else navigateBack();
});

/**
 * Builds the __entity__ from the form and sends it through the store.
 * @returns {void}
 */
function save__Entity__() {
  const __entity__ = new __Entity__({
    id: isEdit.value ? id.value : null,
    name: form.name
  });
  if (isEdit.value) update__Entity__(__entity__);
  else add__Entity__(__entity__);
  navigateBack();
}

/**
 * Returns to the list.
 * @returns {void}
 */
function navigateBack() {
  router.push({name: '__context__-__entities-kebab__'});
}
</script>

<template>
  <section>
    <h1>{{ isEdit ? 'Edit __Entity__' : 'New __Entity__' }}</h1>

    <form @submit.prevent="save__Entity__">
      <label for="name">Name</label>
      <input id="name" v-model="form.name" required type="text"/>

      <button type="submit">{{ isEdit ? 'Update' : 'Create' }}</button>
      <button type="button" @click="navigateBack">Cancel</button>
    </form>
  </section>
</template>
