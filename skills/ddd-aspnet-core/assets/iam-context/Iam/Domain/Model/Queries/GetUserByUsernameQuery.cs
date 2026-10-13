namespace __RootNamespace__.Iam.Domain.Model.Queries;

/// <summary>
///     Get the user with a username.
/// </summary>
/// <param name="Username">The username, as it was typed.</param>
public record GetUserByUsernameQuery(string Username);
