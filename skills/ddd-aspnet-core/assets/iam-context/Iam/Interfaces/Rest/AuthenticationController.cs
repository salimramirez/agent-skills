using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using __RootNamespace__.Iam.Application.CommandServices;
using __RootNamespace__.Iam.Interfaces.Rest.Resources;
using __RootNamespace__.Iam.Interfaces.Rest.Transform;
using __RootNamespace__.Shared.Interfaces.Rest.Transform;

namespace __RootNamespace__.Iam.Interfaces.Rest;

/// <summary>
///     Signs users up and in. The only endpoints open without a token.
/// </summary>
/// <param name="userCommandService">Signing up and signing in.</param>
[AllowAnonymous]
[ApiController]
[Route("api/v1/[controller]")]
public class AuthenticationController(IUserCommandService userCommandService) : ControllerBase
{
    /// <summary>
    ///     Signs up a new user.
    /// </summary>
    /// <param name="resource">The username, password and roles.</param>
    /// <param name="cancellationToken">Cancels the request.</param>
    /// <response code="201">The new user.</response>
    /// <response code="400">A value is missing or invalid, or a role does not exist.</response>
    /// <response code="409">The username is taken.</response>
    [HttpPost("sign-up")]
    [ProducesResponseType<UserResource>(StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> SignUp(SignUpResource resource, CancellationToken cancellationToken)
    {
        var command = SignUpCommandFromResourceAssembler.ToCommandFromResource(resource);
        var result = await userCommandService.Handle(command, cancellationToken);
        return result.ToActionResult(this, user => CreatedAtAction(
            nameof(UsersController.GetUserById),
            "Users",
            new { userId = user.Id },
            UserResourceFromEntityAssembler.ToResourceFromEntity(user)));
    }

    /// <summary>
    ///     Signs a user in and returns the bearer token for the other requests.
    /// </summary>
    /// <param name="resource">The username and password.</param>
    /// <param name="cancellationToken">Cancels the request.</param>
    /// <response code="200">The user and the token.</response>
    /// <response code="401">The username or the password is wrong.</response>
    [HttpPost("sign-in")]
    [ProducesResponseType<AuthenticatedUserResource>(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> SignIn(SignInResource resource, CancellationToken cancellationToken)
    {
        var command = SignInCommandFromResourceAssembler.ToCommandFromResource(resource);
        var result = await userCommandService.Handle(command, cancellationToken);
        return result.ToActionResult(this, signedIn => Ok(
            AuthenticatedUserResourceFromEntityAssembler.ToResourceFromEntity(signedIn.User, signedIn.Token)));
    }
}
