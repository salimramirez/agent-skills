namespace __RootNamespace__.Iam.Interfaces.Acl;

/// <summary>
///     What the IAM bounded context offers to the other bounded contexts, in primitives only.
/// </summary>
public interface IIamContextFacade
{
    /// <summary>
    ///     Gets the identity of the user with a username.
    /// </summary>
    /// <param name="username">The username.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>The identity, or <c>null</c> when there is no user with it.</returns>
    Task<int?> FetchUserIdByUsername(string username, CancellationToken cancellationToken);

    /// <summary>
    ///     Gets the username of a user.
    /// </summary>
    /// <param name="userId">The identity of the user.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>The username, or <c>null</c> when there is no user with that identity.</returns>
    Task<string?> FetchUsernameByUserId(int userId, CancellationToken cancellationToken);
}
