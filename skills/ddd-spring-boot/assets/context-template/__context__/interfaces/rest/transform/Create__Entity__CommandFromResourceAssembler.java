package __base_package__.__context__.interfaces.rest.transform;

import __base_package__.__context__.domain.model.commands.Create__Entity__Command;
import __base_package__.__context__.interfaces.rest.resources.Create__Entity__Resource;

/**
 * Assembler to convert a Create__Entity__Resource to a Create__Entity__Command.
 */
public class Create__Entity__CommandFromResourceAssembler {
    /**
     * Converts a Create__Entity__Resource to a Create__Entity__Command.
     *
     * @param resource The {@link Create__Entity__Resource} resource to convert.
     * @return The {@link Create__Entity__Command} command that results from the conversion.
     */
    public static Create__Entity__Command toCommandFromResource(Create__Entity__Resource resource) {
        return new Create__Entity__Command(resource.name());
    }
}
