namespace __RootNamespace__.Shared.Application.Model;

/// <summary>
///     What kind of expected failure a use case ran into. The REST interface turns each kind into one status code.
/// </summary>
public enum ErrorKind
{
    /// <summary>
    ///     What the use case acts on does not exist: <c>404 Not Found</c>.
    /// </summary>
    NotFound,

    /// <summary>
    ///     The request conflicts with what already exists: a username taken, a name repeated. <c>409 Conflict</c>.
    /// </summary>
    Conflict,

    /// <summary>
    ///     The request refers to something it cannot use: a customer that does not exist. <c>400 Bad Request</c>.
    /// </summary>
    Invalid,

    /// <summary>
    ///     The caller could not be authenticated: a wrong username or password. <c>401 Unauthorized</c>.
    /// </summary>
    Unauthorized
}
