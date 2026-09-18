package __base_package__.iam.interfaces.rest.transform;

import __base_package__.iam.domain.model.aggregates.User;
import __base_package__.iam.interfaces.rest.resources.AuthenticatedUserResource;

/**
 * Assembler to convert a User entity and its token to an AuthenticatedUserResource.
 */
public class AuthenticatedUserResourceFromEntityAssembler {
    public static AuthenticatedUserResource toResourceFromEntity(User user, String token) {
        return new AuthenticatedUserResource(user.getId(), user.getUsername(), token);
    }
}