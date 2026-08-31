import type {AxiosResponse} from 'axios';
import {BaseApi, type BaseApiOptions} from '../../shared/infrastructure/base-api';
import {BaseEndpoint} from '../../shared/infrastructure/base-endpoint';
import {__Entity__Assembler} from './__entity-kebab__.assembler';
import type {__Entity__} from '../domain/model/__entity-kebab__.entity';
import type {__Entity__Resource} from './__entity-kebab__.resource';

const __entities__EndpointPath = import.meta.env.VITE___ENTITIES_UPPER___ENDPOINT_PATH;

/**
 * The API of the __context__ bounded context.
 *
 * Owns the endpoints of this context and exposes them as operations named in the
 * ubiquitous language, so the store never holds an endpoint itself. Add one private
 * endpoint field per aggregate the context reads or writes.
 */
export class __Context__Api extends BaseApi {
    readonly #__entities__: BaseEndpoint<__Entity__Resource>;

    constructor(options: BaseApiOptions = {}) {
        super(options);
        this.#__entities__ = new BaseEndpoint<__Entity__Resource>(this.http, __entities__EndpointPath);
    }

    get__Entities__() {
        return this.#__entities__.getAll();
    }

    create__Entity__(__entity__: __Entity__): Promise<AxiosResponse<__Entity__Resource>> {
        return this.#__entities__.create(__Entity__Assembler.toResourceFromEntity(__entity__));
    }

    update__Entity__(__entity__: __Entity__): Promise<AxiosResponse<__Entity__Resource>> {
        return this.#__entities__.update(__entity__.id!, __Entity__Assembler.toResourceFromEntity(__entity__));
    }

    delete__Entity__(id: number): Promise<AxiosResponse<void>> {
        return this.#__entities__.delete(id);
    }
}
