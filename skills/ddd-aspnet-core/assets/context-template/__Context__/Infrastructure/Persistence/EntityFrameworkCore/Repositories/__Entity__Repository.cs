using Microsoft.EntityFrameworkCore;
using __RootNamespace__.__Context__.Domain.Model.Aggregates;
using __RootNamespace__.__Context__.Domain.Repositories;
using __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Configuration;
using __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Repositories;

namespace __RootNamespace__.__Context__.Infrastructure.Persistence.EntityFrameworkCore.Repositories;

/// <summary>
///     The __entities words__, in their table.
/// </summary>
/// <param name="context">The database context.</param>
public class __Entity__Repository(AppDbContext context)
    : BaseRepository<__Entity__>(context), I__Entity__Repository
{
    /// <inheritdoc />
    public async Task<bool> ExistsByNameAsync(
        string name, int excluded__Entity__Id, CancellationToken cancellationToken)
    {
        return await Context.Set<__Entity__>().AnyAsync(
            __entity__ => __entity__.Name == name && __entity__.Id != excluded__Entity__Id, cancellationToken);
    }
}
