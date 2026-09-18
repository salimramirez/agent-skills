package __base_package__.iam.application.internal.commandservices;

import __base_package__.iam.application.internal.outboundservices.hashing.HashingService;
import __base_package__.iam.application.internal.outboundservices.tokens.TokenService;
import __base_package__.iam.domain.exceptions.InvalidCredentialsException;
import __base_package__.iam.domain.model.aggregates.User;
import __base_package__.iam.domain.model.entities.Role;
import __base_package__.iam.domain.model.commands.SignInCommand;
import __base_package__.iam.domain.model.commands.SignUpCommand;
import __base_package__.iam.domain.services.UserCommandService;
import __base_package__.iam.infrastructure.persistence.jpa.repositories.RoleRepository;
import __base_package__.iam.infrastructure.persistence.jpa.repositories.UserRepository;
import org.apache.commons.lang3.tuple.ImmutablePair;
import org.springframework.stereotype.Service;

import java.util.Optional;

/**
 * User command service implementation
 * <p>
 *     This class implements the {@link UserCommandService} interface and provides the implementation for the
 *     {@link SignInCommand} and {@link SignUpCommand} commands.
 * </p>
 */
@Service
public class UserCommandServiceImpl implements UserCommandService {
    private final UserRepository userRepository;
    private final HashingService hashingService;
    private final TokenService tokenService;
    private final RoleRepository roleRepository;

    public UserCommandServiceImpl(UserRepository userRepository, HashingService hashingService, TokenService tokenService, RoleRepository roleRepository) {
        this.userRepository = userRepository;
        this.hashingService = hashingService;
        this.tokenService = tokenService;
        this.roleRepository = roleRepository;
    }

    /**
     * Handle the sign-in command
     * <p>
     *     This method handles the {@link SignInCommand} command and returns the user and the token.
     * </p>
     * @param command the sign-in command containing the username and password
     * @return and optional containing the user matching the username and the generated token
     * @throws InvalidCredentialsException if the user is not found or the password is invalid
     */
    @Override
    public Optional<ImmutablePair<User, String>> handle(SignInCommand command) {
        // The same failure for an unknown username and a wrong password: do not tell an attacker which one it was
        var user = userRepository.findByUsername(command.username())
                .orElseThrow(InvalidCredentialsException::new);
        if (!hashingService.matches(command.password(), user.getPassword()))
            throw new InvalidCredentialsException();
        var token = tokenService.generateToken(user.getUsername());
        return Optional.of(ImmutablePair.of(user, token));
    }

    /**
     * Handle the sign-up command
     * <p>
     *     This method handles the {@link SignUpCommand} command and returns the user.
     * </p>
     * @param command the sign-up command containing the username and password
     * @return the created user
     * @throws IllegalArgumentException if the username is taken or a role does not exist
     */
    @Override
    public Optional<User> handle(SignUpCommand command) {
        if (userRepository.existsByUsername(command.username()))
            throw new IllegalArgumentException("Username %s already exists".formatted(command.username()));
        // Resolve every role - including the default one - to its persisted row, so no transient Role is ever saved
        var roles = Role.validateRoleSet(command.roles()).stream()
                .map(role -> roleRepository.findByName(role.getName())
                        .orElseThrow(() -> new IllegalArgumentException("Role %s not found".formatted(role.getStringName()))))
                .toList();
        var user = new User(command.username(), hashingService.encode(command.password()), roles);
        userRepository.save(user);
        return userRepository.findByUsername(command.username());
    }
}