namespace __RootNamespace__.Iam.Interfaces.Rest.Resources;

/// <summary>
///     A user, as the API returns it. Never the password hash.
/// </summary>
/// <param name="Id">The identity of the user.</param>
/// <param name="Username">The username.</param>
/// <param name="Roles">The role names.</param>
public record UserResource(int Id, string Username, IEnumerable<string> Roles);
