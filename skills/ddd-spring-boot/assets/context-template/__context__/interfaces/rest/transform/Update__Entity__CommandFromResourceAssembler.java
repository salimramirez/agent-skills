package __base_package__.__context__.interfaces.rest.transform;

import __base_package__.__context__.domain.model.commands.Update__Entity__Command;
import __base_package__.__context__.interfaces.rest.resources.Update__Entity__Resource;

/**
 * Assembler to convert an Update__Entity__Resource to an Update__Entity__Command.
 */
public class Update__Entity__CommandFromResourceAssembler {
    /**
     * Converts an Update__Entity__Resource to an Update__Entity__Command.
     *
     * @param __entity__Id The __entity__ id.
     * @param resource The {@link Update__Entity__Resource} resource to convert.
     * @return The {@link Update__Entity__Command} command that results from the conversion.
     */
    public static Update__Entity__Command toCommandFromResource(Long __entity__Id, Update__Entity__Resource resource) {
        return new Update__Entity__Command(__entity__Id, resource.name());
    }
}
