using __RootNamespace__.Shared.Application.Model;

namespace __RootNamespace__.Shared.Interfaces.Rest.Transform;

/// <summary>
///     The one table from a kind of failure to the status code that answers it.
/// </summary>
public static class ErrorKindExtensions
{
    /// <summary>
    ///     Gets the status code that answers a failure of this kind.
    /// </summary>
    /// <param name="kind">The kind of failure.</param>
    /// <returns>404, 409, 400 or 401.</returns>
    public static int ToStatusCode(this ErrorKind kind)
    {
        return kind switch
        {
            ErrorKind.NotFound => StatusCodes.Status404NotFound,
            ErrorKind.Conflict => StatusCodes.Status409Conflict,
            ErrorKind.Invalid => StatusCodes.Status400BadRequest,
            ErrorKind.Unauthorized => StatusCodes.Status401Unauthorized,
            _ => throw new ArgumentOutOfRangeException(nameof(kind), kind, "No status code for this kind of error.")
        };
    }
}
