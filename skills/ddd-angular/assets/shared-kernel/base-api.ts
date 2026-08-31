/**
 * Base for the single service that fronts a bounded context's API.
 *
 * @remarks
 * A context API owns the endpoints of its context and exposes them as named
 * operations, so the store never holds an endpoint itself. There is nothing to
 * inherit yet; extending it states the role.
 */
export abstract class BaseApi {
}
