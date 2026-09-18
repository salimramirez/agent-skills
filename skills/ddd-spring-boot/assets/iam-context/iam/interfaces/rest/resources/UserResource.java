package __base_package__.iam.interfaces.rest.resources;

import java.util.List;

/**
 * User resource.
 */
public record UserResource(Long id, String username, List<String> roles) {
}