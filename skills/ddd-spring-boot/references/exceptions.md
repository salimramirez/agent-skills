# Domain exceptions and error handling

Domain exceptions, and turning them into HTTP responses in one place.

Express failures in the **ubiquitous language**, not as generic errors. Define domain-specific exceptions in `domain/exceptions`, thrown by the domain (or its services) when an invariant breaks or an aggregate is missing:

```java
// domain/exceptions
public class OrderNotFoundException extends RuntimeException {
    public OrderNotFoundException(OrderId id) {
        super("Order with id %s not found".formatted(id.value()));
    }
}
```

Keep these exceptions free of web/HTTP concerns — no status codes inside them. That preserves domain purity and lets the same exception surface over REST, messaging, or a CLI.

Translate them to transport responses at the edge, in **one place**: a `@RestControllerAdvice` in the interfaces layer maps each exception to a status code, so controllers stay clean.

```java
// interfaces/rest — one handler for the whole app
@RestControllerAdvice
class GlobalExceptionHandler {

    @ExceptionHandler(OrderNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    ErrorResponse handle(OrderNotFoundException ex) {
        return ErrorResponse.create(ex, HttpStatusCode.valueOf(404), ex.getMessage());
    }

    @ExceptionHandler(IllegalArgumentException.class)   // e.g. value-object validation failures
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    ErrorResponse handle(IllegalArgumentException ex) {
        return ErrorResponse.create(ex, HttpStatusCode.valueOf(400), ex.getMessage());
    }
}
```

This pairs a clear domain vocabulary for failures with a single, centralized place that decides how each failure looks to the outside.
