using __RootNamespace__.__Context__.Application.QueryServices;
using __RootNamespace__.__Context__.Domain.Model.Aggregates;
using __RootNamespace__.__Context__.Domain.Model.Queries;
using __RootNamespace__.__Context__.Domain.Repositories;

namespace __RootNamespace__.__Context__.Application.Internal.QueryServices;

/// <summary>
///     The use cases that read __entities words__.
/// </summary>
/// <param name="__entity__Repository">The __entities words__.</param>
public class __Entity__QueryService(I__Entity__Repository __entity__Repository) : I__Entity__QueryService
{
    /// <inheritdoc />
    public async Task<__Entity__?> Handle(Get__Entity__ByIdQuery query, CancellationToken cancellationToken)
    {
        return await __entity__Repository.FindByIdAsync(query.__Entity__Id, cancellationToken);
    }

    /// <inheritdoc />
    public async Task<IEnumerable<__Entity__>> Handle(
        GetAll__Entities__Query query, CancellationToken cancellationToken)
    {
        return await __entity__Repository.ListAsync(cancellationToken);
    }
}
