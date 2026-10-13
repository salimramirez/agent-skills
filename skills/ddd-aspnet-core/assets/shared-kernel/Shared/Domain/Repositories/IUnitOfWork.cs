namespace __RootNamespace__.Shared.Domain.Repositories;

/// <summary>
///     Commits the changes of a use case as one transaction.
/// </summary>
public interface IUnitOfWork
{
    /// <summary>
    ///     Saves every change made through the repositories, then dispatches the domain events the changed
    ///     aggregates raised.
    /// </summary>
    /// <param name="cancellationToken">Cancels the operation.</param>
    Task CompleteAsync(CancellationToken cancellationToken = default);
}
