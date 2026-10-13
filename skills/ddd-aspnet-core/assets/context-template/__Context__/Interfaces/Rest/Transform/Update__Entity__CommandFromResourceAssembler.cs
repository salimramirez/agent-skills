using __RootNamespace__.__Context__.Domain.Model.Commands;
using __RootNamespace__.__Context__.Interfaces.Rest.Resources;

namespace __RootNamespace__.__Context__.Interfaces.Rest.Transform;

/// <summary>
///     Builds an <see cref="Update__Entity__Command" /> from the route and the body of the request.
/// </summary>
public static class Update__Entity__CommandFromResourceAssembler
{
    /// <summary>
    ///     Builds the command.
    /// </summary>
    /// <param name="__entity__Id">The __entity words__, from the route.</param>
    /// <param name="resource">The body of the request.</param>
    /// <returns>The command.</returns>
    public static Update__Entity__Command ToCommandFromResource(int __entity__Id, Update__Entity__Resource resource)
    {
        return new Update__Entity__Command(__entity__Id, resource.Name);
    }
}
