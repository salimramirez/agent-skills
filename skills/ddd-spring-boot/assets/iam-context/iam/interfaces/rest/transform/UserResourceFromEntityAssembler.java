package __base_package__.iam.interfaces.rest.transform;

import __base_package__.iam.domain.model.aggregates.User;
import __base_package__.iam.domain.model.entities.Role;
import __base_package__.iam.interfaces.rest.resources.UserResource;

/**
 * UserResourceFromEntityAssembler
 * @summary
 * Assembler to convert a User entity to a UserResource.
 */
public class UserResourceFromEntityAssembler {
    public static UserResource toResourceFromEntity(User user) {
        var roles = user.getRoles().stream().map(Role::getStringName).toList();
        return new UserResource(user.getId(), user.getUsername(), roles);
    }
}