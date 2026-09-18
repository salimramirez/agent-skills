package __base_package__.iam.domain.services;

import __base_package__.iam.domain.model.commands.SeedRolesCommand;

/**
 * Role command service
 * @summary
 * This interface represents the service to handle role commands.
 */
public interface RoleCommandService {
    /**
     * Handle seed roles command
     * @param command the {@link SeedRolesCommand} command
     *
     */
    void handle(SeedRolesCommand command);
}