# Domain exceptions and error handling

Failures named in the ubiquitous language, and one place per scope that turns them into HTTP responses.

## Four kinds of failure

| The situation | What is thrown | Where | Becomes |
| --- | --- | --- | --- |
| Input that cannot be right: a blank name, a negative quantity, a price in the wrong currency | `IllegalArgumentException` | records (commands, queries, resources, value objects), the aggregate | 400 |
| An action the aggregate's current state forbids: placing a placed order | `IllegalStateException` | the aggregate | 409 |
| A named thing that does not exist | a domain exception, `OrderNotFoundException` | the command service (`orElseThrow`) | 404 |
| Something this context cannot express with the three above | a domain exception, `InvalidCredentialsException` | wherever the rule lives | whatever the context's advice says |

Anything else — a bare `RuntimeException`, an `Exception` caught and rethrown as something vaguer — is a smell.

## Domain exceptions

In `domain/exceptions`, extending `RuntimeException`, with a constructor that takes what is needed to say what went wrong and builds the message itself. No status code, no HTTP anywhere near it:

```java
public class OrderNotFoundException extends RuntimeException {
    public OrderNotFoundException(Long orderId) {
        super("Order with id %s not found".formatted(orderId));
    }
}
```

The service throws it from the `Optional`:

```java
        return orderRepository.findById(command.orderId()).map(order -> {
            order.place();
            orderRepository.save(order);
            return order.getId();
        }).orElseThrow(() -> new OrderNotFoundException(command.orderId()));
```

A query returns `Optional.empty()` rather than throwing — a read that finds nothing is not an error, and the controller answers 404 itself. A command throws, because a command that names a missing aggregate cannot proceed and the controller should never have to check.

## Two advices, two scopes

The shared kernel handles what every context throws the same way:

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(IllegalArgumentException.class)
    public ErrorResponse handleException(IllegalArgumentException exception) {
        return ErrorResponse.create(exception, HttpStatus.BAD_REQUEST, exception.getMessage());
    }

    @ExceptionHandler(IllegalStateException.class)
    public ErrorResponse handleException(IllegalStateException exception) {
        return ErrorResponse.create(exception, HttpStatus.CONFLICT, exception.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ErrorResponse handleException(MethodArgumentNotValidException exception) {
        var message = exception.getFieldErrors().stream()
                .map(fieldError -> "%s %s".formatted(fieldError.getField(), fieldError.getDefaultMessage()))
                .collect(Collectors.joining("; "));
        return ErrorResponse.create(exception, HttpStatus.BAD_REQUEST, message);
    }
}
```

Each context handles its own exceptions in its own advice, in `interfaces/rest`, limited to its package so that two contexts can never fight over the same type:

```java
@RestControllerAdvice(basePackages = "com.quickbite.platform.ordering")
public class OrderingExceptionHandler {

    @ExceptionHandler(OrderNotFoundException.class)
    public ErrorResponse handleException(OrderNotFoundException exception) {
        return ErrorResponse.create(exception, HttpStatus.NOT_FOUND, exception.getMessage());
    }

    @ExceptionHandler(CustomerNotFoundException.class)
    public ErrorResponse handleException(CustomerNotFoundException exception) {
        return ErrorResponse.create(exception, HttpStatus.NOT_FOUND, exception.getMessage());
    }
}
```

`ErrorResponse.create` produces an RFC 9457 problem detail, which is what the client sees:

```json
{"type":"about:blank","title":"Not Found","status":404,"detail":"Order with id 99 not found","instance":"/api/v1/orders/99/placements"}
```

The `detail` is the exception's message, which is why the messages are written for a reader: `"Only a placed order can be cancelled"` tells the client what to do; `"Invalid state"` does not.

## What the controller still checks

Only the empty `Optional` from a query (`ResponseEntity.notFound().build()`) and the `0L`/`null` id a create could return (`ResponseEntity.badRequest().build()`). Every other status comes from an advice, and a controller with a `try` in it has taken a job that is not its own.
