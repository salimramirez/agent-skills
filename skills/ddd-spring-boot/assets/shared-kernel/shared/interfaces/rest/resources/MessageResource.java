package __base_package__.shared.interfaces.rest.resources;

/**
 * Message Resource
 * @summary
 * A plain message returned by endpoints that have nothing else to return, such as a
 * state transition or a delete.
 * @since 1.0
 */
public record MessageResource(String message) {
}
