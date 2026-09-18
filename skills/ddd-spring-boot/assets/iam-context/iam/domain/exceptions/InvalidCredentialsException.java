package __base_package__.iam.domain.exceptions;

/**
 * Exception thrown when a sign-in fails.
 * @summary
 * Raised for an unknown username and for a wrong password alike, so the response never says
 * which of the two was wrong.
 * @see RuntimeException
 */
public class InvalidCredentialsException extends RuntimeException {
    public InvalidCredentialsException() {
        super("Invalid username or password");
    }
}
