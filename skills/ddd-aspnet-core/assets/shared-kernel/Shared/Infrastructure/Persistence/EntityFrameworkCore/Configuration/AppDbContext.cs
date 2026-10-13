using __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Configuration.Extensions;
using Microsoft.EntityFrameworkCore;

namespace __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Configuration;

/// <summary>
///     The one database context of the platform, shared by every bounded context.
/// </summary>
/// <remarks>
///     Each bounded context maps its aggregates in its own <see cref="IEntityTypeConfiguration{TEntity}" />
///     classes, under <c>Infrastructure/Persistence/EntityFrameworkCore/Configuration</c>; this context picks
///     them all up, so adding a bounded context never means editing it.
/// </remarks>
/// <param name="options">The options the context was registered with.</param>
public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    /// <inheritdoc />
    protected override void ConfigureConventions(ModelConfigurationBuilder configurationBuilder)
    {
        base.ConfigureConventions(configurationBuilder);

        // Enums are stored by name: a reordered enum must not change what the rows mean.
        configurationBuilder.Properties<Enum>().HaveConversion<string>();

        // Timestamps to the microsecond: without it MySQL's datetime keeps whole seconds.
        configurationBuilder.Properties<DateTimeOffset>().HavePrecision(6);
    }

    /// <inheritdoc />
    protected override void OnModelCreating(ModelBuilder builder)
    {
        base.OnModelCreating(builder);

        builder.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);
        builder.IgnoreDomainEvents();

        // Last, so it renames what every configuration above produced.
        builder.UseSnakeCaseNamingConvention();
    }
}
