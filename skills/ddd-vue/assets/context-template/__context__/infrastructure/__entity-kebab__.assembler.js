import {__Entity__} from '../domain/model/__entity-kebab__.entity.js';

/**
 * One __entity__ exactly as the API sends it. Name every field the wire
 * carries, in the wire's own spelling -- this is the only declaration of that
 * shape anywhere, so a mistyped field here becomes a reported error instead of
 * an undefined that reaches a view.
 *
 * @typedef {Object} __Entity__ApiResource
 * @property {number} id
 * @property {string} name
 */

/**
 * Anti-corruption layer between the __entities__ API and the __context__ model.
 *
 * @remarks
 * The only place that knows both the wire shape and the domain shape. Methods
 * are static because an assembler holds no state -- it is a translation, not a
 * collaborator. Field renames, nullable columns and envelope quirks stop here
 * and never reach the store or a view.
 *
 * @class __Entity__Assembler
 */
export class __Entity__Assembler {
    /**
     * Builds one entity from a resource payload.
     *
     * @param {__Entity__ApiResource} resource - Resource as the API returned it.
     * @returns {__Entity__} The entity the rest of the app works with.
     */
    static toEntityFromResource(resource) {
        return new __Entity__({...resource});
    }

    /**
     * Builds the collection from a response, tolerating both wire shapes.
     *
     * @remarks
     * A bare array and an envelope keyed by the resource name both occur in the
     * wild, so accept either. A non-200 yields an empty collection rather than a
     * throw: the store already records the error, and a view rendering nothing
     * beats a view that crashes.
     *
     * @param {import('axios').AxiosResponse<Array<Object>|Object>} response - The response.
     * @returns {__Entity__[]} The entities it carried.
     */
    static toEntitiesFromResponse(response) {
        if (response.status !== 200) return [];
        const resources = response.data instanceof Array
            ? response.data
            : response.data['__entities__'];
        return resources.map(resource => this.toEntityFromResource(resource));
    }
}
