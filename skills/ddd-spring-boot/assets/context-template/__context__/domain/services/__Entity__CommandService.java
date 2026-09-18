package __base_package__.__context__.domain.services;

import __base_package__.__context__.domain.model.aggregates.__Entity__;
import __base_package__.__context__.domain.model.commands.Create__Entity__Command;
import __base_package__.__context__.domain.model.commands.Delete__Entity__Command;
import __base_package__.__context__.domain.model.commands.Update__Entity__Command;

import java.util.Optional;

/**
 * __Entity__CommandService
 * Service that handles __entity__ commands
 */
public interface __Entity__CommandService {
    /**
     * Handle a create __entity__ command
     * @param command The create __entity__ command containing the __entity__ data
     * @return The id of the created __entity__
     * @see Create__Entity__Command
     */
    Long handle(Create__Entity__Command command);

    /**
     * Handle an update __entity__ command
     * @param command The update __entity__ command containing the __entity__ data
     * @return The updated __entity__
     * @see Update__Entity__Command
     */
    Optional<__Entity__> handle(Update__Entity__Command command);

    /**
     * Handle a delete __entity__ command
     * @param command The delete __entity__ command containing the __entity__ id
     * @see Delete__Entity__Command
     */
    void handle(Delete__Entity__Command command);
}
