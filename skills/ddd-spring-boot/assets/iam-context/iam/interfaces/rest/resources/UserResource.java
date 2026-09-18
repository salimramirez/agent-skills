package __base_package__.iam.interfaces.rest.resources;

import java.util.List;

/**
 * UserResource
 * @summary
 * User resource.
 */
public record UserResource(Long id, String username, List<String> roles) {
}