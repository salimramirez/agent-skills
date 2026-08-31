import axios from 'axios';

const platformApiUrl = import.meta.env.VITE_PLATFORM_API_URL;

/**
 * Base for the single gateway that fronts a bounded context's API.
 *
 * @remarks
 * A context API extends this to inherit one configured Axios instance, and
 * composes {@link BaseEndpoint} clients on top of it. Keeping the instance
 * private means no store or view can reach the transport directly.
 *
 * Cross-cutting request handling belongs to the caller, not to this class: pass
 * interceptors in rather than importing them here, so the shared kernel never
 * depends on a bounded context.
 *
 * @class BaseApi
 */
export class BaseApi {
    #http;

    /**
     * @param {Object} [options] - Gateway options.
     * @param {string} [options.baseUrl] - Base URL; defaults to `VITE_PLATFORM_API_URL`.
     * @param {Array<function(Object): Object>} [options.requestInterceptors] - Functions
     *   applied to every outgoing request config, in order.
     */
    constructor({baseUrl = platformApiUrl, requestInterceptors = []} = {}) {
        this.#http = axios.create({
            baseURL: baseUrl,
            headers: {'Content-Type': 'application/json'}
        });
        requestInterceptors.forEach(interceptor => this.#http.interceptors.request.use(interceptor));
    }

    /**
     * The configured Axios instance, for the endpoints this gateway composes.
     *
     * @returns {import('axios').AxiosInstance} Configured Axios instance.
     */
    get http() {
        return this.#http;
    }
}
