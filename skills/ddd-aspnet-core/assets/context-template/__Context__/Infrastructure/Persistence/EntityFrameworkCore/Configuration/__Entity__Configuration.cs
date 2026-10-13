using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using __RootNamespace__.__Context__.Domain.Model.Aggregates;

namespace __RootNamespace__.__Context__.Infrastructure.Persistence.EntityFrameworkCore.Configuration;

/// <summary>
///     Maps <see cref="__Entity__" /> to its table.
/// </summary>
public class __Entity__Configuration : IEntityTypeConfiguration<__Entity__>
{
    /// <inheritdoc />
    public void Configure(EntityTypeBuilder<__Entity__> builder)
    {
        builder.HasKey(__entity__ => __entity__.Id);
        builder.Property(__entity__ => __entity__.Id).ValueGeneratedOnAdd();
        builder.Property(__entity__ => __entity__.Name).HasMaxLength(__Entity__.NameMaxLength).IsRequired();
        builder.HasIndex(__entity__ => __entity__.Name).IsUnique();
    }
}
