import type {AxiosInstance, AxiosResponse} from 'axios';

/**
 * CRUD client for one REST resource of a bounded context.
 *
 * This is the repository of the frontend. It speaks HTTP and nothing else: every
 * method resolves to the raw `AxiosResponse`, and turning that into domain entities
 * is the assembler's job, called from the store. Keeping the two apart is what lets
 * one endpoint serve a collection whose envelope or pagination changes without
 * touching the model.
 *
 * @typeParam TResource - Wire shape of a single item.
 */
export class BaseEndpoint<TResource> {
    // Declared and assigned explicitly rather than as constructor parameter
    // properties: Vite's React + TypeScript template enables `erasableSyntaxOnly`,
    // which rejects any syntax that emits code rather than being stripped.
    private readonly http: AxiosInstance;
    private readonly endpointPath: string;

    constructor(http: AxiosInstance, endpointPath: string) {
        this.http = http;
        this.endpointPath = endpointPath;
    }

    /** Reads the whole collection. */
    getAll(): Promise<AxiosResponse<TResource[] | Record<string, TResource[]>>> {
        return this.http.get(this.endpointPath);
    }

    /** Reads one resource by its identity. */
    getById(id: number | string): Promise<AxiosResponse<TResource>> {
        return this.http.get(`${this.endpointPath}/${id}`);
    }

    /** Creates a resource. */
    create(resource: unknown): Promise<AxiosResponse<TResource>> {
        return this.http.post(this.endpointPath, resource);
    }

    /** Updates a resource. */
    update(id: number | string, resource: unknown): Promise<AxiosResponse<TResource>> {
        return this.http.put(`${this.endpointPath}/${id}`, resource);
    }

    /** Deletes a resource. */
    delete(id: number | string): Promise<AxiosResponse<void>> {
        return this.http.delete(`${this.endpointPath}/${id}`);
    }
}
