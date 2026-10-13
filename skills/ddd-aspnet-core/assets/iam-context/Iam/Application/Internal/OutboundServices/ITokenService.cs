using __RootNamespace__.Iam.Domain.Model.Aggregates;

namespace __RootNamespace__.Iam.Application.Internal.OutboundServices;

/// <summary>
///     Issues the bearer token a signed-in user sends with every request. The use cases depend on this port;
///     the token format is an adapter in infrastructure.
/// </summary>
public interface ITokenService
{
    /// <summary>
    ///     Issues a token for a user.
    /// </summary>
    /// <param name="user">The user who signed in.</param>
    /// <returns>The token.</returns>
    string GenerateToken(User user);
}
