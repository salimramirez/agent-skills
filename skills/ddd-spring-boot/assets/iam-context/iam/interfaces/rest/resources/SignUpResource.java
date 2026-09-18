package __base_package__.iam.interfaces.rest.resources;

import java.util.List;

/**
 * Sign-up resource. Roles are optional; a missing or empty list gets the default role.
 */
public record SignUpResource(String username, String password, List<String> roles) {
}