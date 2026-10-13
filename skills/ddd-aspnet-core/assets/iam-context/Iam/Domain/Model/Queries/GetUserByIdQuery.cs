namespace __RootNamespace__.Iam.Domain.Model.Queries;

/// <summary>
///     Get one user by its identity.
/// </summary>
/// <param name="UserId">The identity of the user.</param>
public record GetUserByIdQuery(int UserId);
