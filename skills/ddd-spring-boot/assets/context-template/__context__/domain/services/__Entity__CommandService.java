package __base_package__.__context__.domain.services;

import __base_package__.__context__.domain.model.aggregates.__Entity__;
import __base_package__.__context__.domain.model.commands.Create__Entity__Command;
import __base_package__.__context__.domain.model.commands.Delete__Entity__Command;
import __base_package__.__context__.domain.model.commands.Update__Entity__Command;

import java.util.Optional;

/**
 * __Entity__CommandService
 * Service that handles __entity words__ commands
 */
public interface __Entity__CommandService {
    /**
     * Handle a create __entity words__ command
     * @param command The create __entity words__ command containing the __entity words__ data
     * @return The id of the created __entity words__
     * @see Create__Entity__Command
     */
    Long handle(Create__Entity__Command command);

    /**
     * Handle an update __entity words__ command
     * @param command The update __entity words__ command containing the __entity words__ data
     * @return The updated __entity words__
     * @see Update__Entity__Command
     */
    Optional<__Entity__> handle(Update__Entity__Command command);

    /**
     * Handle a delete __entity words__ command
     * @param command The delete __entity words__ command containing the __entity words__ id
     * @see Delete__Entity__Command
     */
    void handle(Delete__Entity__Command command);
}
