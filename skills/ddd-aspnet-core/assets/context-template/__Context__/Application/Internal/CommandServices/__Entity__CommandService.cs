using __RootNamespace__.__Context__.Application.CommandServices;
using __RootNamespace__.__Context__.Domain.Model.Aggregates;
using __RootNamespace__.__Context__.Domain.Model.Commands;
using __RootNamespace__.__Context__.Domain.Repositories;
using __RootNamespace__.Shared.Application.Model;
using __RootNamespace__.Shared.Domain.Repositories;

namespace __RootNamespace__.__Context__.Application.Internal.CommandServices;

/// <summary>
///     The use cases that change __entities words__.
/// </summary>
/// <param name="__entity__Repository">The __entities words__.</param>
/// <param name="unitOfWork">Commits each use case.</param>
public class __Entity__CommandService(I__Entity__Repository __entity__Repository, IUnitOfWork unitOfWork)
    : I__Entity__CommandService
{
    /// <inheritdoc />
    public async Task<Result<__Entity__>> Handle(Create__Entity__Command command, CancellationToken cancellationToken)
    {
        var __entity__ = new __Entity__(command);
        if (await __entity__Repository.ExistsByNameAsync(__entity__.Name, 0, cancellationToken))
            return Result<__Entity__>.Conflict($"__A_entity__ named '{__entity__.Name}' already exists.");

        await __entity__Repository.AddAsync(__entity__, cancellationToken);
        await unitOfWork.CompleteAsync(cancellationToken);
        return Result<__Entity__>.Success(__entity__);
    }

    /// <inheritdoc />
    public async Task<Result<__Entity__>> Handle(Update__Entity__Command command, CancellationToken cancellationToken)
    {
        var __entity__ = await __entity__Repository.FindByIdAsync(command.__Entity__Id, cancellationToken);
        if (__entity__ is null)
            return Result<__Entity__>.NotFound($"__Entity words__ {command.__Entity__Id} was not found.");

        __entity__.UpdateInformation(command.Name);
        if (await __entity__Repository.ExistsByNameAsync(__entity__.Name, __entity__.Id, cancellationToken))
            return Result<__Entity__>.Conflict($"__A_entity__ named '{__entity__.Name}' already exists.");

        await unitOfWork.CompleteAsync(cancellationToken);
        return Result<__Entity__>.Success(__entity__);
    }

    /// <inheritdoc />
    public async Task<Result> Handle(Delete__Entity__Command command, CancellationToken cancellationToken)
    {
        var __entity__ = await __entity__Repository.FindByIdAsync(command.__Entity__Id, cancellationToken);
        if (__entity__ is null) return Result.NotFound($"__Entity words__ {command.__Entity__Id} was not found.");

        __entity__Repository.Remove(__entity__);
        await unitOfWork.CompleteAsync(cancellationToken);
        return Result.Success();
    }
}
