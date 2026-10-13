using __RootNamespace__.Iam.Domain.Model.Aggregates;
using __RootNamespace__.Shared.Domain.Repositories;

namespace __RootNamespace__.Iam.Domain.Repositories;

/// <summary>
///     The users who can sign in.
/// </summary>
public interface IUserRepository : IBaseRepository<User>
{
    /// <summary>
    ///     Finds the user with a username.
    /// </summary>
    /// <param name="username">The username, normalized.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>The user, or <c>null</c> when there is none with it.</returns>
    Task<User?> FindByUsernameAsync(string username, CancellationToken cancellationToken);

    /// <summary>
    ///     Gets whether a user has a username.
    /// </summary>
    /// <param name="username">The username, normalized.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns><c>true</c> when it is taken.</returns>
    Task<bool> ExistsByUsernameAsync(string username, CancellationToken cancellationToken);
}
