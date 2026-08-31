/**
 * CRUD client for one REST resource of a bounded context.
 *
 * @remarks
 * This is the repository of the frontend. It speaks HTTP and nothing else: every
 * method resolves to the raw `AxiosResponse`, and turning that into domain
 * entities is the assembler's job, called from the store. Keeping the two apart
 * is what lets one endpoint serve a collection whose response envelope, error
 * shape, or pagination changes without touching the model.
 *
 * @class BaseEndpoint
 */
export class BaseEndpoint {
    /**
     * @param {import('./base-api.js').BaseApi} baseApi - Gateway owning the HTTP client.
     * @param {string} endpointPath - Path of this resource, e.g. `/orders`.
     */
    constructor(baseApi, endpointPath) {
        this.http = baseApi.http;
        this.endpointPath = endpointPath;
    }

    /**
     * Reads the whole collection.
     * @returns {Promise<import('axios').AxiosResponse<Array<Object>|Object>>} The response.
     */
    getAll() {
        return this.http.get(this.endpointPath);
    }

    /**
     * Reads one resource by its identity.
     * @param {number|string} id - Resource identifier.
     * @returns {Promise<import('axios').AxiosResponse<Object>>} The response.
     */
    getById(id) {
        return this.http.get(`${this.endpointPath}/${id}`);
    }

    /**
     * Creates a resource.
     * @param {Object} resource - Body to send.
     * @returns {Promise<import('axios').AxiosResponse<Object>>} The response.
     */
    create(resource) {
        return this.http.post(this.endpointPath, resource);
    }

    /**
     * Updates a resource.
     * @param {number|string} id - Resource identifier.
     * @param {Object} resource - Body carrying the new state.
     * @returns {Promise<import('axios').AxiosResponse<Object>>} The response.
     */
    update(id, resource) {
        return this.http.put(`${this.endpointPath}/${id}`, resource);
    }

    /**
     * Deletes a resource.
     * @param {number|string} id - Resource identifier.
     * @returns {Promise<import('axios').AxiosResponse<void>>} The response.
     */
    delete(id) {
        return this.http.delete(`${this.endpointPath}/${id}`);
    }
}
