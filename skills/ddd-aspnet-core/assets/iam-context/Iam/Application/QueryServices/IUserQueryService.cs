using __RootNamespace__.Iam.Domain.Model.Aggregates;
using __RootNamespace__.Iam.Domain.Model.Queries;

namespace __RootNamespace__.Iam.Application.QueryServices;

/// <summary>
///     The use cases that read users.
/// </summary>
public interface IUserQueryService
{
    /// <summary>
    ///     Gets one user.
    /// </summary>
    /// <param name="query">Which user.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>The user, or <c>null</c> when there is none with that identity.</returns>
    Task<User?> Handle(GetUserByIdQuery query, CancellationToken cancellationToken);

    /// <summary>
    ///     Gets every user.
    /// </summary>
    /// <param name="query">The query.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>All the users.</returns>
    Task<IEnumerable<User>> Handle(GetAllUsersQuery query, CancellationToken cancellationToken);

    /// <summary>
    ///     Gets the user with a username.
    /// </summary>
    /// <param name="query">Which username.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>The user, or <c>null</c> when there is none with it.</returns>
    Task<User?> Handle(GetUserByUsernameQuery query, CancellationToken cancellationToken);
}
