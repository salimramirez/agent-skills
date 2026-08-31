import {BaseApi} from '../../shared/infrastructure/base-api.js';
import {BaseEndpoint} from '../../shared/infrastructure/base-endpoint.js';

const __entities__EndpointPath = import.meta.env.VITE___ENTITIES_UPPER___ENDPOINT_PATH;

/**
 * The API of the __context__ bounded context.
 *
 * @remarks
 * Owns the endpoints of this context and exposes them as operations named in the
 * ubiquitous language, so the store never holds an endpoint itself. Add one
 * private endpoint field per aggregate the context reads or writes.
 *
 * @class __Context__Api
 * @extends BaseApi
 */
export class __Context__Api extends BaseApi {
    #__entities__Endpoint;

    /**
     * @param {Object} [options] - Forwarded to {@link BaseApi}, including interceptors.
     */
    constructor(options = {}) {
        super(options);
        this.#__entities__Endpoint = new BaseEndpoint(this, __entities__EndpointPath);
    }

    /**
     * @returns {Promise<import('axios').AxiosResponse<Array<Object>|Object>>} Every __entity__.
     */
    get__Entities__() {
        return this.#__entities__Endpoint.getAll();
    }

    /**
     * @param {number|string} id - Identity of the __entity__.
     * @returns {Promise<import('axios').AxiosResponse<Object>>} The response.
     */
    get__Entity__ById(id) {
        return this.#__entities__Endpoint.getById(id);
    }

    /**
     * @param {import('../domain/model/__entity-kebab__.entity.js').__Entity__} __entity__ - Entity to create.
     * @returns {Promise<import('axios').AxiosResponse<Object>>} The response.
     */
    create__Entity__(__entity__) {
        return this.#__entities__Endpoint.create(__entity__);
    }

    /**
     * @param {import('../domain/model/__entity-kebab__.entity.js').__Entity__} __entity__ - Entity carrying the new state.
     * @returns {Promise<import('axios').AxiosResponse<Object>>} The response.
     */
    update__Entity__(__entity__) {
        return this.#__entities__Endpoint.update(__entity__.id, __entity__);
    }

    /**
     * @param {number|string} id - Identity of the __entity__ to delete.
     * @returns {Promise<import('axios').AxiosResponse<void>>} The response.
     */
    delete__Entity__(id) {
        return this.#__entities__Endpoint.delete(id);
    }
}
