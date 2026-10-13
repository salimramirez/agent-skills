using Humanizer;

namespace __RootNamespace__.Shared.Infrastructure.Interfaces.AspNetCore.Configuration;

/// <summary>
///     Writes the <c>[controller]</c> and <c>[action]</c> route tokens in kebab-case:
///     <c>MenuItemsController</c> answers at <c>/api/v1/menu-items</c>.
/// </summary>
/// <remarks>
///     Registered in <c>Program.cs</c> through a <c>RouteTokenTransformerConvention</c>.
/// </remarks>
public sealed class KebabCaseParameterTransformer : IOutboundParameterTransformer
{
    /// <inheritdoc />
    public string? TransformOutbound(object? value)
    {
        return value?.ToString()?.Kebaberize();
    }
}
