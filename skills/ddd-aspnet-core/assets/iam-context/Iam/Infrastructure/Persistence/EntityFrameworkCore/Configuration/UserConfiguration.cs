using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.ChangeTracking;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using __RootNamespace__.Iam.Domain.Model.Aggregates;
using __RootNamespace__.Iam.Domain.Model.ValueObjects;

namespace __RootNamespace__.Iam.Infrastructure.Persistence.EntityFrameworkCore.Configuration;

/// <summary>
///     Maps <see cref="User" /> to the <c>users</c> table.
/// </summary>
public class UserConfiguration : IEntityTypeConfiguration<User>
{
    /// <inheritdoc />
    public void Configure(EntityTypeBuilder<User> builder)
    {
        builder.HasKey(user => user.Id);
        builder.Property(user => user.Id).ValueGeneratedOnAdd();
        builder.Property(user => user.Username).HasMaxLength(User.UsernameMaxLength).IsRequired();
        builder.HasIndex(user => user.Username).IsUnique();
        builder.Property(user => user.PasswordHash).HasMaxLength(100).IsRequired();

        // The roles, as names separated by commas in one column. Spelled out because the MySQL provider has
        // no primitive collections: left to its convention it stores the list's ToString() and cannot read
        // the value back.
        builder.Ignore(user => user.Roles);
        builder.Property<List<Role>>("_roles")
            .HasColumnName("Roles")
            .HasConversion(
                roles => string.Join(',', roles),
                value => value.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(Enum.Parse<Role>).ToList(),
                new ValueComparer<List<Role>>(
                    (left, right) => left!.SequenceEqual(right!),
                    roles => roles.Aggregate(0, (hash, role) => HashCode.Combine(hash, role)),
                    roles => roles.ToList()))
            .HasMaxLength(100)
            .IsRequired();
    }
}
