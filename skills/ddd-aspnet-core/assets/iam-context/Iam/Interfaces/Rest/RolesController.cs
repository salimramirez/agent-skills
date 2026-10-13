using Microsoft.AspNetCore.Mvc;
using __RootNamespace__.Iam.Domain.Model.ValueObjects;

namespace __RootNamespace__.Iam.Interfaces.Rest;

/// <summary>
///     Lists the roles a user can have. Requires a bearer token.
/// </summary>
[ApiController]
[Route("api/v1/[controller]")]
public class RolesController : ControllerBase
{
    /// <summary>
    ///     Lists every role name.
    /// </summary>
    /// <response code="200">The role names.</response>
    [HttpGet]
    [ProducesResponseType<IEnumerable<string>>(StatusCodes.Status200OK)]
    public IActionResult GetAllRoles()
    {
        return Ok(Enum.GetValues<Role>().Select(role => role.ToName()));
    }
}
