using __RootNamespace__.__Context__.Domain.Model.Aggregates;
using __RootNamespace__.__Context__.Interfaces.Rest.Resources;

namespace __RootNamespace__.__Context__.Interfaces.Rest.Transform;

/// <summary>
///     Builds the <see cref="__Entity__Resource" /> of __a_entity__.
/// </summary>
public static class __Entity__ResourceFromEntityAssembler
{
    /// <summary>
    ///     Builds the resource.
    /// </summary>
    /// <param name="entity">The __entity words__.</param>
    /// <returns>The resource.</returns>
    public static __Entity__Resource ToResourceFromEntity(__Entity__ entity)
    {
        return new __Entity__Resource(entity.Id, entity.Name);
    }
}
