package __base_package__.iam.interfaces.rest.transform;

import __base_package__.iam.domain.model.commands.SignUpCommand;
import __base_package__.iam.domain.model.entities.Role;
import __base_package__.iam.interfaces.rest.resources.SignUpResource;

import java.util.*;

/**
 * Assembler to convert a SignUpResource to a SignUpCommand.
 */
public class SignUpCommandFromResourceAssembler {
    public static SignUpCommand toCommandFromResource(SignUpResource resource) {
        var roles = resource.roles() != null ? resource.roles().stream().map(name -> Role.toRoleFromName(name)).toList() : new ArrayList<Role>();
        return new SignUpCommand(resource.username(), resource.password(), roles);
    }
}