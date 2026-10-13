using __RootNamespace__.__Context__.Application.CommandServices;
using __RootNamespace__.__Context__.Application.Internal.CommandServices;
using __RootNamespace__.__Context__.Application.Internal.QueryServices;
using __RootNamespace__.__Context__.Application.QueryServices;
using __RootNamespace__.__Context__.Domain.Repositories;
using __RootNamespace__.__Context__.Infrastructure.Persistence.EntityFrameworkCore.Repositories;

namespace __RootNamespace__.__Context__.Infrastructure.DependencyInjection;

/// <summary>
///     Registers the __Context__ bounded context.
/// </summary>
public static class __Context__ContextExtensions
{
    /// <summary>
    ///     Adds the repositories and services of the __Context__ bounded context.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <returns>The same service collection.</returns>
    public static IServiceCollection Add__Context__Context(this IServiceCollection services)
    {
        services.AddScoped<I__Entity__Repository, __Entity__Repository>();
        services.AddScoped<I__Entity__CommandService, __Entity__CommandService>();
        services.AddScoped<I__Entity__QueryService, __Entity__QueryService>();
        return services;
    }
}
