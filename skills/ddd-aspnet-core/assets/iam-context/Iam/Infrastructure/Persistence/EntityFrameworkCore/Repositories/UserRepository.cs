using Microsoft.EntityFrameworkCore;
using __RootNamespace__.Iam.Domain.Model.Aggregates;
using __RootNamespace__.Iam.Domain.Repositories;
using __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Configuration;
using __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Repositories;

namespace __RootNamespace__.Iam.Infrastructure.Persistence.EntityFrameworkCore.Repositories;

/// <summary>
///     The users, in the <c>users</c> table.
/// </summary>
/// <param name="context">The database context.</param>
public class UserRepository(AppDbContext context) : BaseRepository<User>(context), IUserRepository
{
    /// <inheritdoc />
    public async Task<User?> FindByUsernameAsync(string username, CancellationToken cancellationToken)
    {
        return await Context.Set<User>().FirstOrDefaultAsync(user => user.Username == username, cancellationToken);
    }

    /// <inheritdoc />
    public async Task<bool> ExistsByUsernameAsync(string username, CancellationToken cancellationToken)
    {
        return await Context.Set<User>().AnyAsync(user => user.Username == username, cancellationToken);
    }
}
