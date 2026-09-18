package __base_package__.__context__.interfaces.rest;

import __base_package__.__context__.domain.exceptions.__Entity__NotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.web.ErrorResponse;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * __Context__ExceptionHandler
 * @summary
 * Maps the domain exceptions of this bounded context to HTTP responses, so the controllers
 * never see them. The generic failures - invalid input - are handled once for the whole
 * application in the shared GlobalExceptionHandler.
 */
@RestControllerAdvice(basePackages = "__base_package__.__context__")
public class __Context__ExceptionHandler {

    /**
     * Handles __Entity__NotFoundException.
     * @param exception The {@link __Entity__NotFoundException} exception to handle
     * @return The {@link ErrorResponse} error response
     */
    @ExceptionHandler(__Entity__NotFoundException.class)
    public ErrorResponse handleException(__Entity__NotFoundException exception) {
        return ErrorResponse.create(exception, HttpStatus.NOT_FOUND, exception.getMessage());
    }
}
