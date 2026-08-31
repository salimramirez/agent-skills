import {defineStore} from 'pinia';
import {computed, ref} from 'vue';
import {__Context__Api} from '../infrastructure/__context__-api.js';
import {__Entity__Assembler} from '../infrastructure/__entity-kebab__.assembler.js';

const __context__Api = new __Context__Api();

/**
 * State and use cases of the __context__ bounded context.
 *
 * @remarks
 * The store is the only thing that talks to {@link __Context__Api}, and the only
 * place an assembler is called: the endpoint returns a raw response, and turning
 * it into entities is an application concern. Views read state and dispatch
 * actions; they never see a response.
 *
 * @returns {Object} State and actions exposed to the presentation layer.
 */
const use__Context__Store = defineStore('__context__', () => {
    /** @type {import('vue').Ref<Array<import('../domain/model/__entity-kebab__.entity.js').__Entity__>>} Loaded __entities__. */
    const __entities__ = ref([]);
    /** @type {import('vue').Ref<Array<Error>>} Errors from failed calls, newest last. */
    const errors = ref([]);
    /** @type {import('vue').Ref<boolean>} Whether __entities__ have been fetched at least once. */
    const __entities__Loaded = ref(false);
    /** @type {import('vue').ComputedRef<number>} How many __entities__ are loaded. */
    const __entities__Count = computed(() => __entities__.value.length);

    /**
     * Loads every __entity__ from the API.
     * @returns {void}
     */
    function fetch__Entities__() {
        __context__Api.get__Entities__()
            .then(response => {
                __entities__.value = __Entity__Assembler.toEntitiesFromResponse(response);
                __entities__Loaded.value = true;
            })
            .catch(error => errors.value.push(error));
    }

    /**
     * Finds one loaded __entity__ by identity.
     *
     * @param {number|string} id - Identity to look up; a route param arrives as a string.
     * @returns {?import('../domain/model/__entity-kebab__.entity.js').__Entity__} The entity, or undefined.
     */
    function get__Entity__ById(id) {
        const numericId = Number(id);
        return __entities__.value.find(__entity__ => __entity__.id === numericId);
    }

    /**
     * Creates a __entity__ and adds it to the collection.
     * @param {import('../domain/model/__entity-kebab__.entity.js').__Entity__} __entity__ - Entity built by the form.
     * @returns {void}
     */
    function add__Entity__(__entity__) {
        __context__Api.create__Entity__(__entity__)
            .then(response => {
                __entities__.value.push(__Entity__Assembler.toEntityFromResource(response.data));
            })
            .catch(error => errors.value.push(error));
    }

    /**
     * Updates a __entity__ in place.
     * @param {import('../domain/model/__entity-kebab__.entity.js').__Entity__} __entity__ - Entity carrying the new state.
     * @returns {void}
     */
    function update__Entity__(__entity__) {
        __context__Api.update__Entity__(__entity__)
            .then(response => {
                const updated = __Entity__Assembler.toEntityFromResource(response.data);
                const index = __entities__.value.findIndex(current => current.id === updated.id);
                if (index !== -1) __entities__.value[index] = updated;
            })
            .catch(error => errors.value.push(error));
    }

    /**
     * Deletes a __entity__ and drops it from the collection.
     * @param {import('../domain/model/__entity-kebab__.entity.js').__Entity__} __entity__ - Entity to remove.
     * @returns {void}
     */
    function delete__Entity__(__entity__) {
        __context__Api.delete__Entity__(__entity__.id)
            .then(() => {
                const index = __entities__.value.findIndex(current => current.id === __entity__.id);
                if (index !== -1) __entities__.value.splice(index, 1);
            })
            .catch(error => errors.value.push(error));
    }

    return {
        __entities__,
        errors,
        __entities__Loaded,
        __entities__Count,
        fetch__Entities__,
        get__Entity__ById,
        add__Entity__,
        update__Entity__,
        delete__Entity__
    };
});

export default use__Context__Store;
