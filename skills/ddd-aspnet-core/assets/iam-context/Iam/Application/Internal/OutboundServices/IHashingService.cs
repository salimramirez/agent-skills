namespace __RootNamespace__.Iam.Application.Internal.OutboundServices;

/// <summary>
///     Hashes passwords and checks them against a hash. The use cases depend on this port; the algorithm is
///     an adapter in infrastructure.
/// </summary>
public interface IHashingService
{
    /// <summary>
    ///     Hashes a password.
    /// </summary>
    /// <param name="password">The password.</param>
    /// <returns>The hash, with its salt and parameters.</returns>
    string HashPassword(string password);

    /// <summary>
    ///     Checks a password against a hash.
    /// </summary>
    /// <param name="password">The password.</param>
    /// <param name="passwordHash">The hash it should match.</param>
    /// <returns><c>true</c> when it matches.</returns>
    bool VerifyPassword(string password, string passwordHash);
}
