package __base_package__.iam.domain.model.commands;

/**
 * Sign in command
 * <p>
 *     This class represents the command to sign in a user.
 * </p>
 * @param username the username of the user
 * @param password the password of the user
 *
 * @see __base_package__.iam.domain.model.aggregates.User
 */
public record SignInCommand(String username, String password) {
    /**
     * Constructor
     * @throws IllegalArgumentException if username or password is null or blank
     */
    public SignInCommand {
        if (username == null || username.isBlank())
            throw new IllegalArgumentException("username cannot be null or blank");
        if (password == null || password.isBlank())
            throw new IllegalArgumentException("password cannot be null or blank");
    }
}