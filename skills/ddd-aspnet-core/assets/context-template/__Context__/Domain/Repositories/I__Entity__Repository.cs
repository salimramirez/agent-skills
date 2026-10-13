using __RootNamespace__.__Context__.Domain.Model.Aggregates;
using __RootNamespace__.Shared.Domain.Repositories;

namespace __RootNamespace__.__Context__.Domain.Repositories;

/// <summary>
///     The __entities words__ of the __Context__ bounded context.
/// </summary>
public interface I__Entity__Repository : IBaseRepository<__Entity__>
{
    /// <summary>
    ///     Gets whether __a_entity__ other than the one given has a name.
    /// </summary>
    /// <param name="name">The name.</param>
    /// <param name="excluded__Entity__Id">__A_entity__ to leave out of the check; <c>0</c> to check them all.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns><c>true</c> when the name is taken.</returns>
    Task<bool> ExistsByNameAsync(string name, int excluded__Entity__Id, CancellationToken cancellationToken);
}
