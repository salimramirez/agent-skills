using __RootNamespace__.Iam.Domain.Model.Aggregates;
using __RootNamespace__.Iam.Interfaces.Rest.Resources;

namespace __RootNamespace__.Iam.Interfaces.Rest.Transform;

/// <summary>
///     Builds an <see cref="AuthenticatedUserResource" /> from a <see cref="User" /> and its token.
/// </summary>
public static class AuthenticatedUserResourceFromEntityAssembler
{
    /// <summary>
    ///     Builds the resource.
    /// </summary>
    /// <param name="entity">The user who signed in.</param>
    /// <param name="token">The bearer token issued to them.</param>
    /// <returns>The resource.</returns>
    public static AuthenticatedUserResource ToResourceFromEntity(User entity, string token)
    {
        return new AuthenticatedUserResource(entity.Id, entity.Username, token);
    }
}
