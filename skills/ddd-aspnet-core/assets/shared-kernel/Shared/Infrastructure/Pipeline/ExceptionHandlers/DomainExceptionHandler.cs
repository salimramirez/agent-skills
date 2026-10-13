using Microsoft.AspNetCore.Diagnostics;
using Microsoft.EntityFrameworkCore;
using __RootNamespace__.Shared.Application.Model;
using __RootNamespace__.Shared.Domain.Model.Exceptions;
using __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Extensions;
using __RootNamespace__.Shared.Interfaces.Rest.Transform;

namespace __RootNamespace__.Shared.Infrastructure.Pipeline.ExceptionHandlers;

/// <summary>
///     Answers the exceptions that are not bugs with a problem details body (RFC 9457): a value the domain
///     rejected (400), a rule the aggregate enforced (409), a save that lost a race with another one (409), a
///     value a unique index already held (409).
/// </summary>
/// <remarks>
///     Anything else is left to the default handler, which answers <c>500</c> and logs it.
/// </remarks>
/// <param name="problemDetailsService">Writes the problem details body.</param>
public sealed class DomainExceptionHandler(IProblemDetailsService problemDetailsService) : IExceptionHandler
{
    private const string LostRace = "Another request changed this resource first. Read it again and retry.";

    /// <inheritdoc />
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
