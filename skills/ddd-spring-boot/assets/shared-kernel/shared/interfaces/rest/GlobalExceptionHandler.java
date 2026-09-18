package __base_package__.shared.interfaces.rest;

import org.springframework.http.HttpStatus;
import org.springframework.web.ErrorResponse;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.stream.Collectors;

/**
 * Global exception handler for the application.
 * @summary
 * Turns the failures that are not specific to any bounded context into HTTP responses in one
 * place: an {@link IllegalArgumentException} - the way commands, queries, value objects and
 * resources reject invalid input - becomes a 400 Bad Request, and so does a Bean Validation
 * failure on a request body; an {@link IllegalStateException} - the way an aggregate refuses a
 * transition its current state does not allow - becomes a 409 Conflict. Each context maps its
 * own domain exceptions in its own advice.
 * @since 1.0
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * Handles IllegalArgumentException.
     * @param exception The {@link IllegalArgumentException} exception to handle
     * @return The {@link ErrorResponse} error response
     */
    @ExceptionHandler(IllegalArgumentException.class)
    public ErrorResponse handleException(IllegalArgumentException exception) {
        return ErrorResponse.create(exception, HttpStatus.BAD_REQUEST, exception.getMessage());
    }

    /**
     * Handles IllegalStateException.
     * @param exception The {@link IllegalStateException} exception to handle
     * @return The {@link ErrorResponse} error response
     */
    @ExceptionHandler(IllegalStateException.class)
    public ErrorResponse handleException(IllegalStateException exception) {
        return ErrorResponse.create(exception, HttpStatus.CONFLICT, exception.getMessage());
    }

    /**
     * Handles MethodArgumentNotValidException.
     * @param exception The {@link MethodArgumentNotValidException} exception to handle
     * @return The {@link ErrorResponse} error response
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ErrorResponse handleException(MethodArgumentNotValidException exception) {
        var message = exception.getFieldErrors().stream()
                .map(fieldError -> "%s %s".formatted(fieldError.getField(), fieldError.getDefaultMessage()))
                .collect(Collectors.joining("; "));
        return ErrorResponse.create(exception, HttpStatus.BAD_REQUEST, message);
    }
}
