using Microsoft.AspNetCore.Mvc;
using __RootNamespace__.Iam.Application.QueryServices;
using __RootNamespace__.Iam.Domain.Model.Queries;
using __RootNamespace__.Iam.Interfaces.Rest.Resources;
using __RootNamespace__.Iam.Interfaces.Rest.Transform;

namespace __RootNamespace__.Iam.Interfaces.Rest;

/// <summary>
///     Reads users. Requires a bearer token.
/// </summary>
/// <param name="userQueryService">The use cases that read users.</param>
[ApiController]
[Route("api/v1/[controller]")]
public class UsersController(IUserQueryService userQueryService) : ControllerBase
{
    /// <summary>
    ///     Gets a user.
    /// </summary>
    /// <param name="userId">The identity of the user.</param>
    /// <param name="cancellationToken">Cancels the request.</param>
    /// <response code="200">The user.</response>
    /// <response code="404">There is no user with that identity.</response>
    [HttpGet("{userId:int}")]
    [ProducesResponseType<UserResource>(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetUserById(int userId, CancellationToken cancellationToken)
    {
        var user = await userQueryService.Handle(new GetUserByIdQuery(userId), cancellationToken);
        if (user is null)
            return Problem(detail: $"User {userId} was not found.", statusCode: StatusCodes.Status404NotFound);
        return Ok(UserResourceFromEntityAssembler.ToResourceFromEntity(user));
    }

    /// <summary>
    ///     Lists every user.
    /// </summary>
    /// <param name="cancellationToken">Cancels the request.</param>
    /// <response code="200">The users.</response>
    [HttpGet]
    [ProducesResponseType<IEnumerable<UserResource>>(StatusCodes.Status200OK)]
    public async Task<IActionResult> GetAllUsers(CancellationToken cancellationToken)
    {
        var users = await userQueryService.Handle(new GetAllUsersQuery(), cancellationToken);
        return Ok(users.Select(UserResourceFromEntityAssembler.ToResourceFromEntity));
    }
}
