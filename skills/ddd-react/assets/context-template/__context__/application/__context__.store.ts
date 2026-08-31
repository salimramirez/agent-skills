import {create} from 'zustand';
import {__Context__Api} from '../infrastructure/__context__-api';
import {__Entity__Assembler} from '../infrastructure/__entity-kebab__.assembler';
import type {__Entity__} from '../domain/model/__entity-kebab__.entity';

const __context__Api = new __Context__Api();

/** State and use cases of the __context__ bounded context. */
export interface __Context__State {
    __entities__: __Entity__[];
    errors: Error[];
    __entities__Loaded: boolean;
    fetch__Entities__: () => Promise<void>;
    add__Entity__: (__entity__: __Entity__) => Promise<void>;
    update__Entity__: (__entity__: __Entity__) => Promise<void>;
    delete__Entity__: (id: number) => Promise<void>;
}

/**
 * The application layer of the __context__ context.
 *
 * The only thing that talks to the gateway, and the only place an assembler is
 * called: the endpoint hands back a raw response, and turning it into domain objects
 * is an application concern. It imports nothing from React, so it can be exercised
 * without rendering — read it outside a component with
 * `use__Context__Store.getState()`, which is what makes loaders and interceptors work.
 *
 * Every update replaces state rather than mutating it. React compares by reference.
 */
export const use__Context__Store = create<__Context__State>()((set, get) => ({
    __entities__: [],
    errors: [],
    __entities__Loaded: false,

    fetch__Entities__: async () => {
        try {
            const response = await __context__Api.get__Entities__();
            set({
                __entities__: __Entity__Assembler.toEntitiesFromResponse(response),
                __entities__Loaded: true
            });
        } catch (error) {
            set({errors: [...get().errors, error as Error]});
        }
    },

    add__Entity__: async (__entity__: __Entity__) => {
        try {
            const response = await __context__Api.create__Entity__(__entity__);
            const created = __Entity__Assembler.toEntityFromResource(response.data);
            set({__entities__: [...get().__entities__, created]});
        } catch (error) {
            set({errors: [...get().errors, error as Error]});
        }
    },

    update__Entity__: async (__entity__: __Entity__) => {
        try {
            const response = await __context__Api.update__Entity__(__entity__);
            const updated = __Entity__Assembler.toEntityFromResource(response.data);
            set({
                __entities__: get().__entities__.map(current =>
                    current.id === updated.id ? updated : current)
            });
        } catch (error) {
            set({errors: [...get().errors, error as Error]});
        }
    },

    delete__Entity__: async (id: number) => {
        try {
            await __context__Api.delete__Entity__(id);
            set({__entities__: get().__entities__.filter(current => current.id !== id)});
        } catch (error) {
            set({errors: [...get().errors, error as Error]});
        }
    }
}));
