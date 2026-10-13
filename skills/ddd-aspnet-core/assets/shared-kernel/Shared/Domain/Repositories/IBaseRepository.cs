namespace __RootNamespace__.Shared.Domain.Repositories;

/// <summary>
///     The operations every repository has: a collection of aggregates of one type.
/// </summary>
/// <remarks>
///     There is no <c>Update</c>: an aggregate loaded through a repository is tracked, and the unit of work
///     saves whatever changed in it.
/// </remarks>
/// <typeparam name="TEntity">The aggregate root the repository holds.</typeparam>
public interface IBaseRepository<TEntity> where TEntity : class
{
    /// <summary>
    ///     Adds a new aggregate. It is inserted when the unit of work completes.
    /// </summary>
    /// <param name="entity">The aggregate to add.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    Task AddAsync(TEntity entity, CancellationToken cancellationToken = default);

    /// <summary>
    ///     Finds an aggregate by its identity, whole: with every entity inside it.
    /// </summary>
    /// <param name="id">The identity of the aggregate.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>The aggregate, or <c>null</c> when there is none with that identity.</returns>
    Task<TEntity?> FindByIdAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    ///     Removes an aggregate. It is deleted when the unit of work completes.
    /// </summary>
    /// <param name="entity">The aggregate to remove.</param>
    void Remove(TEntity entity);

    /// <summary>
    ///     Lists every aggregate.
    /// </summary>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>All the aggregates, possibly none.</returns>
    Task<IEnumerable<TEntity>> ListAsync(CancellationToken cancellationToken = default);
}
