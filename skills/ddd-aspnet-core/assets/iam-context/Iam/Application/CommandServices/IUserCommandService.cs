using __RootNamespace__.Iam.Domain.Model.Aggregates;
using __RootNamespace__.Iam.Domain.Model.Commands;
using __RootNamespace__.Shared.Application.Model;

namespace __RootNamespace__.Iam.Application.CommandServices;

/// <summary>
///     Signing up and signing in.
/// </summary>
public interface IUserCommandService
{
    /// <summary>
    ///     Signs up a new user.
    /// </summary>
    /// <param name="command">The username, password and roles.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>The new user, or a conflict when the username is taken.</returns>
    Task<Result<User>> Handle(SignUpCommand command, CancellationToken cancellationToken);

    /// <summary>
    ///     Signs a user in.
    /// </summary>
    /// <param name="command">The username and password.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>
    ///     The user and a bearer token; or unauthorized, the same for an unknown username as for a wrong password.
    /// </returns>
    Task<Result<(User User, string Token)>> Handle(SignInCommand command, CancellationToken cancellationToken);
}
