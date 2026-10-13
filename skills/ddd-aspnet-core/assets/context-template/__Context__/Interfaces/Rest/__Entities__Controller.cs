using Microsoft.AspNetCore.Mvc;
using __RootNamespace__.__Context__.Application.CommandServices;
using __RootNamespace__.__Context__.Application.QueryServices;
using __RootNamespace__.__Context__.Domain.Model.Commands;
using __RootNamespace__.__Context__.Domain.Model.Queries;
using __RootNamespace__.__Context__.Interfaces.Rest.Resources;
using __RootNamespace__.__Context__.Interfaces.Rest.Transform;
using __RootNamespace__.Shared.Interfaces.Rest.Transform;

namespace __RootNamespace__.__Context__.Interfaces.Rest;

/// <summary>
///     Creates, reads, updates and deletes __entities words__.
/// </summary>
/// <param name="__entity__CommandService">The use cases that change __entities words__.</param>
/// <param name="__entity__QueryService">The use cases that read __entities words__.</param>
[ApiController]
[Route("api/v1/[controller]")]
public class __Entities__Controller(
    I__Entity__CommandService __entity__CommandService,
    I__Entity__QueryService __entity__QueryService) : ControllerBase
{
    /// <summary>
    ///     Gets __a_entity__.
    /// </summary>
    /// <param name="__entity__Id">The identity of the __entity words__.</param>
    /// <param name="cancellationToken">Cancels the request.</param>
    /// <response code="200">The __entity words__.</response>
    /// <response code="404">There is no __entity words__ with that identity.</response>
    [HttpGet("{__entity__Id:int}")]
    [ProducesResponseType<__Entity__Resource>(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Get__Entity__ById(int __entity__Id, CancellationToken cancellationToken)
    {
        var query = new Get__Entity__ByIdQuery(__entity__Id);
        var __entity__ = await __entity__QueryService.Handle(query, cancellationToken);
        if (__entity__ is null)
            return Problem(
                detail: $"__Entity words__ {__entity__Id} was not found.", statusCode: StatusCodes.Status404NotFound);
        return Ok(__Entity__ResourceFromEntityAssembler.ToResourceFromEntity(__entity__));
    }

    /// <summary>
    ///     Lists every __entity words__.
    /// </summary>
    /// <param name="cancellationToken">Cancels the request.</param>
    /// <response code="200">The __entities words__, possibly none.</response>
    [HttpGet]
    [ProducesResponseType<IEnumerable<__Entity__Resource>>(StatusCodes.Status200OK)]
    public async Task<IActionResult> GetAll__Entities__(CancellationToken cancellationToken)
    {
        var __entities__ = await __entity__QueryService.Handle(new GetAll__Entities__Query(), cancellationToken);
        return Ok(__entities__.Select(__Entity__ResourceFromEntityAssembler.ToResourceFromEntity));
    }

    /// <summary>
    ///     Creates __a_entity__.
    /// </summary>
    /// <param name="resource">The __entity words__ to create.</param>
    /// <param name="cancellationToken">Cancels the request.</param>
    /// <response code="201">The new __entity words__.</response>
    /// <response code="400">A value is missing or invalid.</response>
    /// <response code="409">The name is taken.</response>
    [HttpPost]
    [ProducesResponseType<__Entity__Resource>(StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> Create__Entity__(
        Create__Entity__Resource resource, CancellationToken cancellationToken)
    {
        var command = Create__Entity__CommandFromResourceAssembler.ToCommandFromResource(resource);
        var result = await __entity__CommandService.Handle(command, cancellationToken);
        return result.ToActionResult(this, __entity__ => CreatedAtAction(
            nameof(Get__Entity__ById),
            new { __entity__Id = __entity__.Id },
            __Entity__ResourceFromEntityAssembler.ToResourceFromEntity(__entity__)));
    }

    /// <summary>
    ///     Replaces the information of __a_entity__.
    /// </summary>
    /// <param name="__entity__Id">The identity of the __entity words__.</param>
    /// <param name="resource">The new information.</param>
    /// <param name="cancellationToken">Cancels the request.</param>
    /// <response code="200">The updated __entity words__.</response>
    /// <response code="400">A value is missing or invalid.</response>
    /// <response code="404">There is no __entity words__ with that identity.</response>
    /// <response code="409">The name is taken.</response>
    [HttpPut("{__entity__Id:int}")]
    [ProducesResponseType<__Entity__Resource>(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> Update__Entity__(
        int __entity__Id, Update__Entity__Resource resource, CancellationToken cancellationToken)
    {
        var command = Update__Entity__CommandFromResourceAssembler.ToCommandFromResource(__entity__Id, resource);
        var result = await __entity__CommandService.Handle(command, cancellationToken);
        return result.ToActionResult(this,
            __entity__ => Ok(__Entity__ResourceFromEntityAssembler.ToResourceFromEntity(__entity__)));
    }

    /// <summary>
    ///     Deletes __a_entity__.
    /// </summary>
    /// <param name="__entity__Id">The identity of the __entity words__.</param>
    /// <param name="cancellationToken">Cancels the request.</param>
    /// <response code="204">The __entity words__ was deleted.</response>
    /// <response code="404">There is no __entity words__ with that identity.</response>
    [HttpDelete("{__entity__Id:int}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete__Entity__(int __entity__Id, CancellationToken cancellationToken)
    {
        var command = new Delete__Entity__Command(__entity__Id);
        var result = await __entity__CommandService.Handle(command, cancellationToken);
        return result.ToActionResult(this, NoContent);
    }
}
