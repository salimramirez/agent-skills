namespace __RootNamespace__.Shared.Infrastructure.Interfaces.AspNetCore.Configuration;

/// <summary>
///     Names the schemas of the API description after the bounded context that owns them —
///     <c>Ordering.OrderResource</c> — so two contexts can each have a resource with the same name.
/// </summary>
public static class OpenApiSchemaIds
{
    /// <summary>
    ///     Gets the schema id of a type: <c>Context.TypeName</c> for a type of a bounded context, the plain type
    ///     name for anything else (<c>ProblemDetails</c>).
    /// </summary>
    /// <param name="type">The type a schema describes.</param>
    /// <returns>The schema id.</returns>
    public static string For(Type type)
    {
        var name = type.IsGenericType
            ? $"{type.Name[..type.Name.IndexOf('`')]}Of{string.Join("And", type.GetGenericArguments().Select(For))}"
            : type.Name;
        var ns = type.Namespace ?? string.Empty;
        var layer = ns.IndexOf(".Interfaces.", StringComparison.Ordinal);
        return layer < 0 ? name : $"{ns[..layer].Split('.')[^1]}.{name}";
    }
}
