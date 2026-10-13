# Errors and problem details

The kinds of failure, where each one becomes a status code, and how every failure leaves the application as an RFC 9457 problem details body.

## Two mechanisms, one rule for choosing

- **A rule of the domain that is broken is an exception.** An email that is not an email, an order placed with no lines: the domain refuses, whoever asks, and a refusal must not be ignorable. A constructor cannot return anything else, and a result that a caller forgets to read compiles without a warning (measured).
- **An outcome a use case can expect is a result.** The order to place does not exist; the username is taken; the customer an order names does not exist; the password is wrong. The command service returns `Result<T>`, the signature says so, and the controller answers it.
- **A query that finds nothing returns `null`.** The controller answers 404.

The domain is the same whichever way the application layer goes: it throws. What the hybrid adds is a typed answer for the outcomes the application layer can name.

## The table

| Failure | Raised as | Status | Answered by |
| --- | --- | --- | --- |
| A value the domain cannot accept | `InvalidValueException` | 400 | `DomainExceptionHandler` |
| An operation the aggregate refuses in its state | `BusinessRuleViolationException` | 409 | `DomainExceptionHandler` |
| Another request saved the same aggregate first | `DbUpdateConcurrencyException`, or a deadlock the database broke | 409 | `DomainExceptionHandler` |
| A value a unique index already holds | `DbUpdateException` from the database | 409 | `DomainExceptionHandler` |
| What the use case acts on does not exist | `Result.NotFound(...)` | 404 | `ToActionResult` |
| The request conflicts with what exists | `Result.Conflict(...)` | 409 | `ToActionResult` |
| The request refers to something unusable | `Result.Invalid(...)` | 400 | `ToActionResult` |
| The caller could not be authenticated | `Result.Unauthorized(...)` | 401 | `ToActionResult` |
| A query found nothing | `null` | 404 | the action, with `Problem(...)` |
| A malformed body | model validation | 400 | `[ApiController]` |
| No valid token; a valid token without the role | the authentication and authorization middleware | 401; 403 | `UseStatusCodePages` |
| Anything else | any other exception | 500 | the default exception handler |

The status of each `ErrorKind` is written once, in `ErrorKindExtensions.ToStatusCode()`, and both `ToActionResult` and `DomainExceptionHandler` use it.

## The domain's exceptions, never the framework's

```csharp
public abstract class DomainException(string message) : Exception(message);
public sealed class InvalidValueException(string message) : DomainException(message);           // 400
public sealed class BusinessRuleViolationException(string message) : DomainException(message);  // 409
```

The domain throws only these. It never throws `ArgumentException` or `InvalidOperationException` to mean "bad input" or "not allowed now", and the handler never maps those to a 4xx: EF Core, LINQ and the dependency injection container throw them for programming errors — `First()` on an empty sequence, an entity tracked twice, a service that cannot be built. Mapped to 400 or 409, a bug would tell the client it was the client's fault, and nobody would look for it.

The message is written for the client, in the ubiquitous language, and becomes the `detail`: "Cannot place an order without lines."

## The exception handler

```csharp
public sealed class DomainExceptionHandler(IProblemDetailsService problemDetailsService) : IExceptionHandler
{
    private const string LostRace = "Another request changed this resource first. Read it again and retry.";

    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext, Exception exception, CancellationToken cancellationToken)
    {
        var error = exception switch
        {
            InvalidValueException => new Error(ErrorKind.Invalid, exception.Message),
            BusinessRuleViolationException => new Error(ErrorKind.Conflict, exception.Message),
            DbUpdateConcurrencyException => new Error(ErrorKind.Conflict, LostRace),
            DbUpdateException deadlock when deadlock.IsDeadlock() => new Error(ErrorKind.Conflict, LostRace),
            DbUpdateException duplicate when duplicate.IsUniqueConstraintViolation() =>
                new Error(ErrorKind.Conflict, "The request conflicts with a value that already exists."),
            _ => null
        };
        if (error is null) return false;

        httpContext.Response.StatusCode = error.Kind.ToStatusCode();
        return await problemDetailsService.TryWriteAsync(new ProblemDetailsContext
        {
            HttpContext = httpContext,
            Exception = exception,
            ProblemDetails = { Status = httpContext.Response.StatusCode, Detail = error.Message }
        });
    }
}
```

- **It answers what it recognizes and returns `false` for the rest**, which the default handler answers with a 500 and logs with its stack trace. The 500's body says nothing about the cause — `"title": "An error occurred while processing your request."` — in development too, because `UseExceptionHandler` catches it before the developer exception page would (measured).
- **A save that lost a race is a 409, not a 500.** Every aggregate root carries a `Version`; of two requests that change the same order at once, the one that commits second finds the version moved and EF Core throws `DbUpdateConcurrencyException` (see `aggregates.md`). On MySQL, two saves that each add a part to one aggregate can deadlock instead, and the database rolls one back; that is the same lost race, with the same answer. Both arms come before the unique-index one: the concurrency exception is a `DbUpdateException` too.
- **A unique-index conflict gets a fixed message.** The database's own ("Duplicate entry 'ana@example.com' for key 'customers.ix_customers_email'") names tables and indexes; the client gets "The request conflicts with a value that already exists."
- **A context with an exception of its own** adds it to this switch, or registers a second `IExceptionHandler` before this one. Most contexts need neither: `InvalidValueException`, `BusinessRuleViolationException` and the results cover them.

## One shape, whoever writes it

Two writers produce problem details: `controller.Problem(...)` — used by `ToActionResult` and by actions answering a `null` — and `IProblemDetailsService` — used by the exception handler, by model validation, and by `UseStatusCodePages` for the bodiless 401, 403 and 404. Measured, they produce the same shape:

```json
{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.10","title":"Conflict","status":409,
 "detail":"A customer is already registered with ana@example.com.","traceId":"00-…-00"}
```

- `type` and `title` are filled from the status; `detail` is the message; `traceId` ties the response to the log entry.
- **The content type is `application/problem+json` for all of them**, as long as no controller declares `[Produces("application/json")]` — with it, the problem details the controller writes leave as `application/json` (measured).
- **One customization reaches all four**: `AddProblemDetails(options => options.CustomizeProblemDetails = context => …)` added its field to the answers of `Problem()`, of the exception handler, of model validation and of `UseStatusCodePages` (measured). Add an `instance`, a link to documentation, an error code there — once.

## What never to do

- **Never `catch (Exception)` in a service** to return a failure: it reports a bug as an expected failure, with the wrong status, and logs nothing.
- **Never catch `OperationCanceledException` to answer it.** When the client disconnects there is no one to answer; ASP.NET Core ends the request without logging an error (measured). A 409 written to a closed connection only hides real conflicts in the logs.
- **Never put the exception's own message in a 500**, nor a stack trace in any response. The log has them; the response has the `traceId`.
- **Never answer an expected failure with 200** and an error in the body. The status is the first thing a client reads.
