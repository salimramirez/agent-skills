/**
 * Marker for the payload an API endpoint returns.
 *
 * @remarks
 * A response is the envelope; a resource is one item inside it. Both shapes
 * mirror the wire format and never leave the infrastructure layer.
 */
export interface BaseResponse {}

/**
 * Contract every API resource satisfies.
 */
export interface BaseResource {
  /**
   * Identity of the resource as the backend reports it.
   */
  id: number;
}
