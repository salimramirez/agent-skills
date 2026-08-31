import axios, {type AxiosInstance, type InternalAxiosRequestConfig} from 'axios';

const platformApiUrl = import.meta.env.VITE_PLATFORM_API_URL;

/** A function applied to every outgoing request config. */
export type RequestInterceptor = (config: InternalAxiosRequestConfig) => InternalAxiosRequestConfig;

/** Options for a context gateway. */
export interface BaseApiOptions {
    /** Base URL; defaults to `VITE_PLATFORM_API_URL`. */
    baseUrl?: string;
    /** Applied to every outgoing request, in order. */
    requestInterceptors?: RequestInterceptor[];
}

/**
 * Base for the single gateway that fronts a bounded context's API.
 *
 * A context API extends this to inherit one configured Axios instance, and composes
 * `BaseEndpoint` clients on top of it. The instance is private, so no store or
 * component can reach the transport directly.
 *
 * Cross-cutting request handling is passed in rather than imported here, so the
 * shared kernel never depends on a bounded context.
 */
export abstract class BaseApi {
    readonly #http: AxiosInstance;

    protected constructor({baseUrl = platformApiUrl, requestInterceptors = []}: BaseApiOptions = {}) {
        this.#http = axios.create({
            baseURL: baseUrl,
            headers: {'Content-Type': 'application/json'}
        });
        requestInterceptors.forEach(interceptor => this.#http.interceptors.request.use(interceptor));
    }

    /** The configured Axios instance, for the endpoints this gateway composes. */
    protected get http(): AxiosInstance {
        return this.#http;
    }
}
