using __RootNamespace__.__Context__.Domain.Model.Aggregates;
using __RootNamespace__.__Context__.Domain.Model.Queries;

namespace __RootNamespace__.__Context__.Application.QueryServices;

/// <summary>
///     The use cases that read __entities words__.
/// </summary>
public interface I__Entity__QueryService
{
    /// <summary>
    ///     Gets one __entity words__.
    /// </summary>
    /// <param name="query">Which __entity words__.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>The __entity words__, or <c>null</c> when there is none with that identity.</returns>
    Task<__Entity__?> Handle(Get__Entity__ByIdQuery query, CancellationToken cancellationToken);

    /// <summary>
    ///     Gets every __entity words__.
    /// </summary>
    /// <param name="query">The query.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>All the __entities words__, possibly none.</returns>
    Task<IEnumerable<__Entity__>> Handle(GetAll__Entities__Query query, CancellationToken cancellationToken);
}
