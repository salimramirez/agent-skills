package __base_package__.iam.domain.services;

import __base_package__.iam.domain.model.aggregates.User;
import __base_package__.iam.domain.model.commands.SignInCommand;
import __base_package__.iam.domain.model.commands.SignUpCommand;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.Optional;

/**
 * User command service
 * @summary
 * This interface represents the service to handle user commands.
 */
public interface UserCommandService {
    /**
     * Handle sign in command
     * @param command the {@link SignInCommand} command
     * @return an {@link Optional} of {@link ImmutablePair} of {@link User} and {@link String}
     */
    Optional<ImmutablePair<User, String>> handle(SignInCommand command);

    /**
     * Handle sign up command
     * @param command the {@link SignUpCommand} command
     * @return an {@link Optional} of {@link User} entity
     */
    Optional<User> handle(SignUpCommand command);
}