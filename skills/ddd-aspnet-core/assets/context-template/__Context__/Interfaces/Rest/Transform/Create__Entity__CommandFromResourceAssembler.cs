using __RootNamespace__.__Context__.Domain.Model.Commands;
using __RootNamespace__.__Context__.Interfaces.Rest.Resources;

namespace __RootNamespace__.__Context__.Interfaces.Rest.Transform;

/// <summary>
///     Builds a <see cref="Create__Entity__Command" /> from the body of the request.
/// </summary>
public static class Create__Entity__CommandFromResourceAssembler
{
    /// <summary>
    ///     Builds the command.
    /// </summary>
    /// <param name="resource">The body of the request.</param>
    /// <returns>The command.</returns>
    public static Create__Entity__Command ToCommandFromResource(Create__Entity__Resource resource)
    {
        return new Create__Entity__Command(resource.Name);
    }
}
