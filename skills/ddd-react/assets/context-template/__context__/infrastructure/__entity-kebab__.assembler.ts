import type {AxiosResponse} from 'axios';
import {__Entity__} from '../domain/model/__entity-kebab__.entity';
import type {__Entity__Resource} from './__entity-kebab__.resource';

/**
 * Anti-corruption layer between the __entities__ API and the __context__ model.
 *
 * The only place that knows both the wire shape and the domain shape. Methods are
 * static because an assembler holds no state — it is a translation, not a
 * collaborator. Renames, nulls and envelope quirks stop here.
 */
export class __Entity__Assembler {
    /** Builds one entity from a resource payload. */
    static toEntityFromResource(resource: __Entity__Resource): __Entity__ {
        return new __Entity__({id: resource.id, name: resource.name});
    }

    /**
     * Builds the collection from a response, tolerating both wire shapes.
     *
     * A bare array and an envelope keyed by the resource name both occur in the wild.
     * A non-200 yields an empty collection rather than a throw: the store already
     * records the error, and a view rendering nothing beats one that crashes.
     */
    static toEntitiesFromResponse(
        response: AxiosResponse<__Entity__Resource[] | Record<string, __Entity__Resource[]>>
    ): __Entity__[] {
        if (response.status !== 200) return [];
        const resources = Array.isArray(response.data)
            ? response.data
            : response.data['__entities__'] ?? [];
        return resources.map(resource => this.toEntityFromResource(resource));
    }

    /** Turns an entity back into the payload the API expects on a write. */
    static toResourceFromEntity(entity: __Entity__): Omit<__Entity__Resource, 'id'> & {id?: number} {
        return {
            ...(entity.id !== null ? {id: entity.id} : {}),
            name: entity.name
        };
    }
}
