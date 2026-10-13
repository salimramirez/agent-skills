namespace __RootNamespace__.Iam.Interfaces.Rest.Resources;

/// <summary>
///     A signed-in user and the bearer token to send with every other request.
/// </summary>
/// <param name="Id">The identity of the user.</param>
/// <param name="Username">The username.</param>
/// <param name="Token">The bearer token.</param>
public record AuthenticatedUserResource(int Id, string Username, string Token);
