package __base_package__.iam.domain.model.commands;

import __base_package__.iam.domain.model.entities.Role;

import java.util.List;

/**
 * Sign up command
 * <p>
 *     This class represents the command to sign up a user.
 * </p>
 * @param username the username of the user
 * @param password the password of the user
 * @param roles the roles of the user
 *
 * @see __base_package__.iam.domain.model.aggregates.User
 */
public record SignUpCommand(String username, String password, List<Role> roles) {
    /**
     * Constructor
     * @throws IllegalArgumentException if username or password is null or blank
     */
    public SignUpCommand {
        if (username == null || username.isBlank())
            throw new IllegalArgumentException("username cannot be null or blank");
        if (password == null || password.isBlank())
            throw new IllegalArgumentException("password cannot be null or blank");
    }
}