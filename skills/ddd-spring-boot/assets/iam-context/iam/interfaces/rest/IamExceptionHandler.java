package __base_package__.iam.interfaces.rest;

import __base_package__.iam.domain.exceptions.InvalidCredentialsException;
import org.springframework.http.HttpStatus;
import org.springframework.web.ErrorResponse;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * IamExceptionHandler
 * @summary
 * Maps the domain exceptions of the IAM bounded context to HTTP responses. Invalid input is
 * handled once for the whole application in the shared GlobalExceptionHandler.
 */
@RestControllerAdvice(basePackages = "__base_package__.iam")
public class IamExceptionHandler {

    /**
     * Handles InvalidCredentialsException.
     * @param exception The {@link InvalidCredentialsException} exception to handle
     * @return The {@link ErrorResponse} error response
     */
    @ExceptionHandler(InvalidCredentialsException.class)
    public ErrorResponse handleException(InvalidCredentialsException exception) {
        return ErrorResponse.create(exception, HttpStatus.UNAUTHORIZED, exception.getMessage());
    }
}
