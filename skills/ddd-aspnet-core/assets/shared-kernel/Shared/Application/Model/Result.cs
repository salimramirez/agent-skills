namespace __RootNamespace__.Shared.Application.Model;

/// <summary>
///     The outcome of a command: the value it produced, or the expected failure that prevented it.
/// </summary>
/// <remarks>
///     A command service returns a failure for what a use case can expect to run into — what it acts on does
///     not exist, or conflicts with what does. A rule of the domain that is broken is not a result: the domain
///     throws, and the exception handler answers it.
/// </remarks>
/// <typeparam name="T">The type of the value a successful command produces.</typeparam>
public sealed class Result<T>
{
    private readonly T? _value;

    private Result(T? value, Error? error)
    {
        _value = value;
        Error = error;
    }

    /// <summary>
    ///     Gets the failure, or <c>null</c> when the command succeeded.
    /// </summary>
    public Error? Error { get; }

    /// <summary>
    ///     Gets whether the command succeeded.
    /// </summary>
    public bool IsSuccess => Error is null;

    /// <summary>
    ///     Gets whether the command failed.
    /// </summary>
    public bool IsFailure => !IsSuccess;

    /// <summary>
    ///     Gets the value the command produced.
    /// </summary>
    /// <exception cref="InvalidOperationException">The command failed; there is no value to read.</exception>
    public T Value => IsSuccess
        ? _value!
        : throw new InvalidOperationException($"A failed result has no value: {Error!.Message}");

    /// <summary>
    ///     A successful outcome carrying the value the command produced.
    /// </summary>
    /// <param name="value">The value.</param>
    public static Result<T> Success(T value)
    {
        return new Result<T>(value, null);
    }

    /// <summary>
    ///     A failed outcome.
    /// </summary>
    /// <param name="error">What prevented the command.</param>
    public static Result<T> Failure(Error error)
    {
        return new Result<T>(default, error);
    }

    /// <summary>
    ///     A failure because what the command acts on does not exist.
    /// </summary>
    /// <param name="message">Which thing was not found.</param>
    public static Result<T> NotFound(string message)
    {
        return Failure(new Error(ErrorKind.NotFound, message));
    }

    /// <summary>
    ///     A failure because the command conflicts with what already exists.
    /// </summary>
    /// <param name="message">What it conflicts with.</param>
    public static Result<T> Conflict(string message)
    {
        return Failure(new Error(ErrorKind.Conflict, message));
    }

    /// <summary>
    ///     A failure because the command refers to something it cannot use.
    /// </summary>
    /// <param name="message">What it cannot use, and why.</param>
    public static Result<T> Invalid(string message)
    {
        return Failure(new Error(ErrorKind.Invalid, message));
    }

    /// <summary>
    ///     A failure because the caller could not be authenticated.
    /// </summary>
    /// <param name="message">What failed, without saying which part.</param>
    public static Result<T> Unauthorized(string message)
    {
        return Failure(new Error(ErrorKind.Unauthorized, message));
    }
}

/// <summary>
///     The outcome of a command that produces no value: success, or the expected failure that prevented it.
/// </summary>
public sealed class Result
{
    private Result(Error? error)
    {
        Error = error;
    }

    /// <summary>
    ///     Gets the failure, or <c>null</c> when the command succeeded.
    /// </summary>
    public Error? Error { get; }

    /// <summary>
    ///     Gets whether the command succeeded.
    /// </summary>
    public bool IsSuccess => Error is null;

    /// <summary>
    ///     Gets whether the command failed.
    /// </summary>
    public bool IsFailure => !IsSuccess;

    /// <summary>
    ///     A successful outcome.
    /// </summary>
    public static Result Success()
    {
        return new Result(null);
    }

    /// <summary>
    ///     A failed outcome.
    /// </summary>
    /// <param name="error">What prevented the command.</param>
    public static Result Failure(Error error)
    {
        return new Result(error);
    }

    /// <summary>
    ///     A failure because what the command acts on does not exist.
    /// </summary>
    /// <param name="message">Which thing was not found.</param>
    public static Result NotFound(string message)
    {
        return Failure(new Error(ErrorKind.NotFound, message));
    }

    /// <summary>
    ///     A failure because the command conflicts with what already exists.
    /// </summary>
    /// <param name="message">What it conflicts with.</param>
    public static Result Conflict(string message)
    {
        return Failure(new Error(ErrorKind.Conflict, message));
    }
}
