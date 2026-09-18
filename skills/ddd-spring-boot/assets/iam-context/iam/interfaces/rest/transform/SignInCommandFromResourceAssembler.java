package __base_package__.iam.interfaces.rest.transform;

import __base_package__.iam.domain.model.commands.SignInCommand;
import __base_package__.iam.interfaces.rest.resources.SignInResource;

/**
 * Assembler to convert a SignInResource to a SignInCommand.
 */
public class SignInCommandFromResourceAssembler {
    public static SignInCommand toCommandFromResource(SignInResource signInResource) {
        return new SignInCommand(signInResource.username(), signInResource.password());
    }
}