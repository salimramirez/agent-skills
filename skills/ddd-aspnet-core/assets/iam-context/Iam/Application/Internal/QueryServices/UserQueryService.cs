using __RootNamespace__.Iam.Application.QueryServices;
using __RootNamespace__.Iam.Domain.Model.Aggregates;
using __RootNamespace__.Iam.Domain.Model.Queries;
using __RootNamespace__.Iam.Domain.Repositories;
using __RootNamespace__.Shared.Domain.Model.Exceptions;

namespace __RootNamespace__.Iam.Application.Internal.QueryServices;

/// <summary>
///     The use cases that read users.
/// </summary>
/// <param name="userRepository">The users.</param>
public class UserQueryService(IUserRepository userRepository) : IUserQueryService
{
    /// <inheritdoc />
    public async Task<User?> Handle(GetUserByIdQuery query, CancellationToken cancellationToken)
    {
        return await userRepository.FindByIdAsync(query.UserId, cancellationToken);
    }

    /// <inheritdoc />
    public async Task<IEnumerable<User>> Handle(GetAllUsersQuery query, CancellationToken cancellationToken)
    {
        return await userRepository.ListAsync(cancellationToken);
    }

    /// <inheritdoc />
    public async Task<User?> Handle(GetUserByUsernameQuery query, CancellationToken cancellationToken)
    {
        try
        {
            return await userRepository.FindByUsernameAsync(User.NormalizeUsername(query.Username), cancellationToken);
        }
        catch (InvalidValueException)
        {
            return null;
        }
    }
}
