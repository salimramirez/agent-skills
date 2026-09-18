package __base_package__.iam.interfaces.rest.resources;

/**
 * Authenticated user resource: the signed-in user and the bearer token to send back.
 */
public record AuthenticatedUserResource(Long id, String username, String token) {
}