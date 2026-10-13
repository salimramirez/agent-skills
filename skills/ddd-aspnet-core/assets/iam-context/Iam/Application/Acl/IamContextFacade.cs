using __RootNamespace__.Iam.Application.QueryServices;
using __RootNamespace__.Iam.Domain.Model.Queries;
using __RootNamespace__.Iam.Interfaces.Acl;

namespace __RootNamespace__.Iam.Application.Acl;

/// <summary>
///     Answers the other bounded contexts through the query service.
/// </summary>
/// <param name="userQueryService">Reads users.</param>
public class IamContextFacade(IUserQueryService userQueryService) : IIamContextFacade
{
    /// <inheritdoc />
    public async Task<int?> FetchUserIdByUsername(string username, CancellationToken cancellationToken)
    {
        var user = await userQueryService.Handle(new GetUserByUsernameQuery(username), cancellationToken);
        return user?.Id;
    }

    /// <inheritdoc />
    public async Task<string?> FetchUsernameByUserId(int userId, CancellationToken cancellationToken)
    {
        var user = await userQueryService.Handle(new GetUserByIdQuery(userId), cancellationToken);
        return user?.Username;
    }
}
