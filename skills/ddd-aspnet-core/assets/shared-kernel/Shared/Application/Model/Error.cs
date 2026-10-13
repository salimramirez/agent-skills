namespace __RootNamespace__.Shared.Application.Model;

/// <summary>
///     An expected failure of a use case: its kind, and a message that says what happened.
/// </summary>
/// <param name="Kind">What kind of failure it is.</param>
/// <param name="Message">What happened, for the client to read.</param>
public sealed record Error(ErrorKind Kind, string Message);
