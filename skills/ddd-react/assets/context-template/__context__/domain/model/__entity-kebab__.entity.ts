/** Attributes a __Entity__ is built from. */
export interface __Entity__Attributes {
    id?: number | null;
    name?: string;
}

/**
 * __Entity__ in the __context__ bounded context.
 *
 * Every field is `readonly`. React decides what to re-render by reference identity,
 * so an entity mutated in place changes nothing on screen — changes produce a new
 * instance through `with…` methods instead.
 *
 * Give it behaviour: a rule that reads only off these fields belongs here, not
 * repeated in every component that needs it. It also strengthens the type check,
 * because a lookalike payload cannot satisfy a class that has methods.
 */
export class __Entity__ {
    readonly id: number | null;
    readonly name: string;

    constructor({id = null, name = ''}: __Entity__Attributes = {}) {
        this.id = id;
        this.name = name;
    }

    /** Whether the backend has assigned this __Entity__ an identity yet. */
    isPersisted(): boolean {
        return this.id !== null;
    }

    /** A copy of this __Entity__ under a different name. */
    withName(name: string): __Entity__ {
        return new __Entity__({...this, name});
    }
}
