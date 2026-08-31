/**
 * __Entity__ in the __context__ bounded context.
 *
 * @remarks
 * Fields are public and the constructor takes one options object with defaults,
 * so `new __Entity__({})` is always a valid, fully-formed object rather than a
 * half-built one. Give it behaviour: a rule that reads off these fields belongs
 * here, not repeated in every view that needs it.
 *
 * @class __Entity__
 */
export class __Entity__ {
    /**
     * @param {Object} params - Entity attributes.
     * @param {?number} [params.id=null] - Identity; null until the backend assigns one.
     * @param {string} [params.name=''] - Name of the __Entity__.
     */
    constructor({id = null, name = ''} = {}) {
        /** @type {?number} Identity; null until the backend assigns one. */
        this.id = id;
        /** @type {string} Name of the __Entity__. */
        this.name = name;
    }

    /**
     * Whether this __entity__ has been persisted yet.
     *
     * @returns {boolean} True once the backend has assigned an identity.
     */
    isPersisted() {
        return this.id !== null;
    }
}
