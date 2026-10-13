using __RootNamespace__.Iam.Domain.Model.Aggregates;
using __RootNamespace__.Iam.Domain.Model.ValueObjects;
using __RootNamespace__.Iam.Interfaces.Rest.Resources;

namespace __RootNamespace__.Iam.Interfaces.Rest.Transform;

/// <summary>
///     Builds a <see cref="UserResource" /> from a <see cref="User" />.
/// </summary>
public static class UserResourceFromEntityAssembler
{
    /// <summary>
    ///     Builds the resource.
    /// </summary>
    /// <param name="entity">The user.</param>
    /// <returns>The resource.</returns>
    public static UserResource ToResourceFromEntity(User entity)
    {
        return new UserResource(entity.Id, entity.Username, entity.Roles.Select(role => role.ToName()));
    }
}
