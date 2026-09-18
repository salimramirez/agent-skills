package __base_package__.iam.interfaces.rest.transform;

import __base_package__.iam.domain.model.entities.Role;
import __base_package__.iam.interfaces.rest.resources.RoleResource;

/**
 * RoleResourceFromEntityAssembler
 * @summary
 * Assembler to convert a Role entity to a RoleResource.
 */
public class RoleResourceFromEntityAssembler {
    public static RoleResource toResourceFromEntity(Role role) {
        return new RoleResource(role.getId(), role.getStringName());
    }
}