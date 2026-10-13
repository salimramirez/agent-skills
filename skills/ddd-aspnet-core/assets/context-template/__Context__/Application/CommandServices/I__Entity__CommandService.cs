using __RootNamespace__.__Context__.Domain.Model.Aggregates;
using __RootNamespace__.__Context__.Domain.Model.Commands;
using __RootNamespace__.Shared.Application.Model;

namespace __RootNamespace__.__Context__.Application.CommandServices;

/// <summary>
///     The use cases that change __entities words__.
/// </summary>
public interface I__Entity__CommandService
{
    /// <summary>
    ///     Creates __a_entity__.
    /// </summary>
    /// <param name="command">The __entity words__ to create.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>The new __entity words__, or a conflict when the name is taken.</returns>
    Task<Result<__Entity__>> Handle(Create__Entity__Command command, CancellationToken cancellationToken);

    /// <summary>
    ///     Replaces the information of __a_entity__.
    /// </summary>
    /// <param name="command">The new information.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>The updated __entity words__; not found, or a conflict when the name is taken.</returns>
    Task<Result<__Entity__>> Handle(Update__Entity__Command command, CancellationToken cancellationToken);

    /// <summary>
    ///     Deletes __a_entity__.
    /// </summary>
    /// <param name="command">Which __entity words__.</param>
    /// <param name="cancellationToken">Cancels the operation.</param>
    /// <returns>Success, or not found.</returns>
    Task<Result> Handle(Delete__Entity__Command command, CancellationToken cancellationToken);
}
