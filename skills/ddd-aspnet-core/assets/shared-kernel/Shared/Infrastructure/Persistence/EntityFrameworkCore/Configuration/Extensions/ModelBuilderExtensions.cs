using Humanizer;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata;
using __RootNamespace__.Shared.Domain.Model.Aggregates;

namespace __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Configuration.Extensions;

/// <summary>
///     Conventions applied to the whole model, after every bounded context has mapped its aggregates.
/// </summary>
public static class ModelBuilderExtensions
{
    /// <summary>
    ///     Keeps the domain events out of the model: they are dispatched, never stored.
    /// </summary>
    /// <param name="builder">The model builder.</param>
    public static void IgnoreDomainEvents(this ModelBuilder builder)
    {
        foreach (var entity in builder.Model.GetEntityTypes()
                     .Where(entity => typeof(AuditableAggregateRoot).IsAssignableFrom(entity.ClrType)))
            builder.Entity(entity.ClrType).Ignore(nameof(AuditableAggregateRoot.DomainEvents));
    }

    /// <summary>
    ///     Names every table in plural snake_case (<c>order_lines</c>) and every column, key, foreign key and
    ///     index in snake_case (<c>customer_id</c>, <c>unit_price_amount</c>, <c>pk_orders</c>).
    /// </summary>
    /// <param name="builder">The model builder.</param>
    public static void UseSnakeCaseNamingConvention(this ModelBuilder builder)
    {
        foreach (var entity in builder.Model.GetEntityTypes())
        {
            var tableName = entity.GetTableName();
            if (string.IsNullOrEmpty(tableName)) continue;

            // Read each column name as it is in its table: a complex property's columns carry its name as a
            // prefix there (UnitPrice_Amount), and the prefix is what keeps two values of one type apart.
            var table = StoreObjectIdentifier.Table(tableName, entity.GetSchema());
            foreach (var property in entity.GetProperties())
                property.SetColumnName(property.GetColumnName(table)!.Underscore());
            foreach (var complexProperty in entity.GetComplexProperties())
                RenameComplexColumns(complexProperty, table);

            entity.SetTableName(tableName.Pluralize(false).Underscore());

            foreach (var key in entity.GetKeys())
                key.SetName(key.GetName()!.Underscore());
            foreach (var foreignKey in entity.GetForeignKeys())
                foreignKey.SetConstraintName(foreignKey.GetConstraintName()!.Underscore());
            foreach (var index in entity.GetIndexes())
                index.SetDatabaseName(index.GetDatabaseName()!.Underscore());
        }
    }

    private static void RenameComplexColumns(IMutableComplexProperty complexProperty, StoreObjectIdentifier table)
    {
        foreach (var property in complexProperty.ComplexType.GetProperties())
            property.SetColumnName(property.GetColumnName(table)!.Underscore());
        foreach (var nested in complexProperty.ComplexType.GetComplexProperties())
            RenameComplexColumns(nested, table);
    }
}
